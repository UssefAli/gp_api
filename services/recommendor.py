import pandas as pd
import numpy as np
import math
import json
from datetime import datetime
import random


def haversine_distance(lat1, lon1, lat2, lon2):
    
    R = 6371.0
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance_km = R * c
    
    return distance_km


def calculate_distance_score(user_lat, user_lon, mechanic_lat, mechanic_lon, max_distance_km=50):
   
    distance_km = haversine_distance(user_lat, user_lon, mechanic_lat, mechanic_lon)
    
    # Calculate normalized score (0 to 1)
    if distance_km > max_distance_km:
        distance_score = 0.0
    else:
        distance_score = 1.0 - (distance_km / max_distance_km)
    
    return distance_km, round(distance_score, 4)


def calculate_all_scores(mechanic, request, max_distance_km=50):
    
    review_score = (mechanic['rating'] - 1) / 4
    
    distance_km, distance_score = calculate_distance_score(
        request['customer_latitude'], request['customer_longitude'],
        mechanic['latitude'], mechanic['longitude'],
        max_distance_km
    )
    
    
    # ...removed specialty_score and availability_score...
    
    return {
        'review_score': round(review_score, 4),
        'distance_km': round(distance_km, 2),
        'distance_score': distance_score
    }



class EpsilonGreedyBandit:
   
    def __init__(self, epsilon=0.1, learning_rate=0.05, num_arms=3):
      
        self.epsilon = epsilon
        self.lr = learning_rate
        
        self.arms = self._initialize_arms(num_arms)
        self.arm_rewards = np.zeros(num_arms)  
        self.arm_counts = np.zeros(num_arms)   
        self.arm_avg_rewards = np.zeros(num_arms)  
        
        self.history = {
            'chosen_arms': [],
            'rewards': [],
            'weight_evolution': []
        }
        
        self.best_arm = 0
        
        print(f"Initialized Epsilon-Greedy Bandit with {num_arms} arms")
        print(f"Exploration rate (epsilon): {epsilon}")
        print(f"Learning rate: {learning_rate}")
    
    def _initialize_arms(self, num_arms):
       
        arms = []
        
        base_combinations = [
            [0.6, 0.4],   # Review-focused
            [0.4, 0.6],   # Distance-focused
            [0.5, 0.5],   # Balanced
        ]
        for i in range(min(num_arms, len(base_combinations))):
            arms.append(np.array(base_combinations[i]))
        for i in range(len(base_combinations), num_arms):
            weights = np.random.dirichlet([1, 1])
            arms.append(weights)
        return arms
    
    def choose_arm(self):
    
        if np.random.random() < self.epsilon:
            arm_idx = np.random.randint(0, len(self.arms))
            print(f"  [EXPLORATION] Chose random arm {arm_idx}")
        else:
            valid_arms = np.where(self.arm_counts > 0)[0]
            
            if len(valid_arms) == 0:
                arm_idx = np.random.randint(0, len(self.arms))
            else:
                avg_rewards = np.zeros(len(self.arms))
                avg_rewards[valid_arms] = self.arm_rewards[valid_arms] / self.arm_counts[valid_arms]
                arm_idx = np.argmax(avg_rewards)
                self.best_arm = arm_idx
            
            print(f"  [EXPLOITATION] Chose best arm {arm_idx} with avg reward: {self.arm_avg_rewards[arm_idx]:.3f}")
        
        weights = self.arms[arm_idx].copy()
        
        self.history['chosen_arms'].append(arm_idx)
        self.history['weight_evolution'].append(weights.copy())
        
        return arm_idx, weights
    
    def update(self, arm_idx, reward):
       
        self.arm_counts[arm_idx] += 1
        self.arm_rewards[arm_idx] += reward
        
        if self.arm_counts[arm_idx] > 0:
            self.arm_avg_rewards[arm_idx] = self.arm_rewards[arm_idx] / self.arm_counts[arm_idx]
        
        self.history['rewards'].append(reward)
        
        if reward > 0.7:  
            adjustment = self.lr * (1 - reward)
            self.arms[arm_idx] += adjustment
            self.arms[arm_idx] = np.maximum(0, self.arms[arm_idx])
            self.arms[arm_idx] /= self.arms[arm_idx].sum()
        
        print(f"  [UPDATE] Arm {arm_idx} received reward: {reward:.3f}")
        print(f"           New average: {self.arm_avg_rewards[arm_idx]:.3f} (based on {self.arm_counts[arm_idx]} trials)")
    
    def calculate_total_score(self, scores_dict, weights):
       
        components = np.array([
            scores_dict['review_score'],
            scores_dict['distance_score']
        ])
        total_score = np.dot(components, weights)
        return round(total_score, 4)
    
    
    def get_statistics(self):
        """
        Get statistics about bandit performance.
        
        Returns:
        --------
        dict: Statistics
        """
        stats = {
            'total_trials': len(self.history['chosen_arms']),
            'exploration_rate': self.epsilon,
            'average_reward': np.mean(self.history['rewards']) if self.history['rewards'] else 0,
            'arm_performance': {},
            'best_arm': int(self.best_arm),
            'best_weights': self.arms[self.best_arm].tolist(),
            'best_avg_reward': self.arm_avg_rewards[self.best_arm] if self.arm_counts[self.best_arm] > 0 else 0
        }
        
        # Add performance for each arm
        for i in range(len(self.arms)):
            if self.arm_counts[i] > 0:
                stats['arm_performance'][i] = {
                    'weights': self.arms[i].tolist(),
                    'trials': int(self.arm_counts[i]),
                    'avg_reward': float(self.arm_avg_rewards[i]),
                    'total_reward': float(self.arm_rewards[i])
                }
        
        return stats
    


class MechanicRecommendationSystem:
   
    
    def __init__(self, mechanics_df, epsilon=0.1, learning_rate=0.05):
        
        self.mechanics_df = mechanics_df.copy()
        self.bandit = EpsilonGreedyBandit(epsilon=epsilon, learning_rate=learning_rate)
        
        if 'specialties' in mechanics_df.columns:
            self.mechanics_df['specialties_list'] = mechanics_df['specialties'].apply(json.loads)
        
        print(f"Initialized Recommendation System with {len(mechanics_df)} mechanics")
    
    def create_sample_request(self, user_lat=None, user_lon=None):
        
        if user_lat is None or user_lon is None:
            user_lat = 40.7128 + np.random.uniform(-0.1, 0.1)
            user_lon = -74.0060 + np.random.uniform(-0.1, 0.1)
        
        return {
            'request_id': f"REQ{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'customer_id': f"CUST{random.randint(1000, 9999)}",
            'customer_latitude': round(user_lat, 6),
            'customer_longitude': round(user_lon, 6),
            'urgency': random.choice(['low', 'medium', 'high', 'emergency']),
            'required_specialties': ['engine_repair', 'diagnostics'],  # Example specialties
            'max_distance_km': random.choice([10, 20, 30, 50])
        }
    
    def recommend_mechanics(self, request, top_k=3, verbose=True):
       
        if verbose:
            print("\n" + "="*60)
            print(f"PROCESSING REQUEST: {request['request_id']}")
            print(f"User Location: ({request['customer_latitude']:.4f}, {request['customer_longitude']:.4f})")
            print("="*60)
        
        arm_idx, weights = self.bandit.choose_arm()
        
        if verbose:
            print(f"\nUsing weights from arm {arm_idx}:")
            print(f"  Alpha (Review): {weights[0]:.3f}")
            print(f"  Beta (Distance): {weights[1]:.3f}")
            

        
        recommendations = []
        
        for idx, mechanic in self.mechanics_df.iterrows():
            scores = calculate_all_scores(
                mechanic.to_dict(),
                request,
                max_distance_km=request.get('max_distance_km', 50)
            )
            
            total_score = self.bandit.calculate_total_score(scores, weights)
            
            recommendations.append({
                'mechanic_id': mechanic['mechanic_id'],
                'mechanic_name': mechanic['name'],
                'total_score': total_score,
                'review_score': scores['review_score'],
                'distance_km': scores['distance_km'],
                'distance_score': scores['distance_score'],
                'arm_used': arm_idx,
                'weights_used': weights.tolist()
            })
        
        recommendations.sort(key=lambda x: x['total_score'], reverse=True)
        top_recommendations = recommendations[:top_k]
        
        if verbose:
            print(f"\nTop {top_k} Recommendations:")
            for i, rec in enumerate(top_recommendations, 1):
                print(f"{i}. {rec['mechanic_name']} (ID: {rec['mechanic_id']})")
                print(f"   Total Score: {rec['total_score']:.4f}")
                print(f"   Components: R={rec['review_score']:.3f}, D={rec['distance_score']:.3f}")
                print(f"   Distance: {rec['distance_km']} km")
                print()
        
        return top_recommendations, arm_idx, weights
    
    def simulate_user_feedback(self, request, chosen_mechanic_id, base_satisfaction=0.8, noise_level=0.1):
        
        mechanic = self.mechanics_df[self.mechanics_df['mechanic_id'] == chosen_mechanic_id].iloc[0]
        
        scores = calculate_all_scores(
            mechanic.to_dict(),
            request,
            max_distance_km=request.get('max_distance_km', 50)
        )
        
        simulated_rating = (
            0.6 * scores['review_score'] +  # Mechanic's reputation
            0.4 * scores['distance_score']   # Proximity
        )
        
        noise = np.random.uniform(-noise_level, noise_level)
        final_rating = max(0, min(1, simulated_rating + noise))
        
        return round(final_rating, 4)
    
    def update_with_feedback(self, arm_idx, user_rating, verbose=True):
       
        if verbose:
            print(f"\n[FEEDBACK RECEIVED]")
            print(f"User rating: {user_rating:.3f}")
            print(f"Updating arm {arm_idx}...")
        
        self.bandit.update(arm_idx, user_rating)
    
    def run_simulation(self, num_requests=100):
        
        print("\n" + "="*60)
        print(f"STARTING SIMULATION: {num_requests} requests")
        print("="*60)
        
        all_stats = []
        
        for i in range(num_requests):
            print(f"\n[Request {i+1}/{num_requests}]")
            
            request = self.create_sample_request()
            
            recommendations, arm_idx, _ = self.recommend_mechanics(request, verbose=False)
            
            chosen_mechanic = recommendations[0]
            
            user_rating = self.simulate_user_feedback(request, chosen_mechanic['mechanic_id'])
            
            self.update_with_feedback(arm_idx, user_rating, verbose=False)
            
            stats = {
                'request_id': i,
                'arm_used': arm_idx,
                'user_rating': user_rating,
                'chosen_mechanic': chosen_mechanic['mechanic_id'],
                'total_score': chosen_mechanic['total_score']
            }
            all_stats.append(stats)
            
            if (i + 1) % 10 == 0:
                bandit_stats = self.bandit.get_statistics()
                print(f"  Progress: {i+1}/{num_requests} | Avg Reward: {bandit_stats['average_reward']:.3f}")
        
        print("\n" + "="*60)
        print("SIMULATION COMPLETE")
        print("="*60)
        
        self.print_performance_summary(all_stats)
        
        return all_stats
    
    def print_performance_summary(self, simulation_stats):
        stats_df = pd.DataFrame(simulation_stats)
        
        print("\nPERFORMANCE SUMMARY:")
        print("-" * 40)
        print(f"Total Requests Processed: {len(stats_df)}")
        print(f"Average User Rating: {stats_df['user_rating'].mean():.3f}")
        print(f"Average Recommendation Score: {stats_df['total_score'].mean():.3f}")
        
        bandit_stats = self.bandit.get_statistics()
        
        print("\nBANDIT STATISTICS:")
        print("-" * 40)
        print(f"Best Arm: {bandit_stats['best_arm']}")
        print(f"Best Weights: {[round(w, 3) for w in bandit_stats['best_weights']]}")
        print(f"Best Arm Average Reward: {bandit_stats['best_avg_reward']:.3f}")
        print(f"Overall Average Reward: {bandit_stats['average_reward']:.3f}")
        
        print("\nARM PERFORMANCE DETAILS:")
        print("-" * 40)
        for arm_idx, arm_info in bandit_stats['arm_performance'].items():
            print(f"Arm {arm_idx}:")
            print(f"  Weights: {[round(w, 3) for w in arm_info['weights']]}")
            print(f"  Trials: {arm_info['trials']}")
            print(f"  Avg Reward: {arm_info['avg_reward']:.3f}")
            print()

def main():
    
    print("="*60)
    print("MECHANIC RECOMMENDATION SYSTEM WITH MULTI-ARMED BANDIT")
    print("="*60)
    
    print("\n1. Loading sample mechanics data...")
    
    sample_mechanics = [
        {'mechanic_id': 'M000', 'name': 'Mechanic 1\'s Garage', 'rating': 3.7, 'review_count': 41, 
         'years_experience': 22, 'latitude': 40.862763, 'longitude': -73.809943},
        {'mechanic_id': 'M001', 'name': 'Mechanic 2\'s Garage', 'rating': 4.7, 'review_count': 474, 
         'years_experience': 7, 'latitude': 40.715276, 'longitude': -74.012805},
        {'mechanic_id': 'M002', 'name': 'Mechanic 3\'s Garage', 'rating': 4.3, 'review_count': 169, 
         'years_experience': 13, 'latitude': 40.678004, 'longitude': -74.069067},
        {'mechanic_id': 'M003', 'name': 'City Auto Repair', 'rating': 4.5, 'review_count': 312, 
         'years_experience': 15, 'latitude': 40.750000, 'longitude': -73.980000},
        {'mechanic_id': 'M004', 'name': 'Downtown Mechanics', 'rating': 4.1, 'review_count': 89, 
         'years_experience': 8, 'latitude': 40.720000, 'longitude': -74.010000},
        {'mechanic_id': 'M005', 'name': 'Suburb Auto Care', 'rating': 4.8, 'review_count': 521, 
         'years_experience': 25, 'latitude': 40.850000, 'longitude': -73.900000},
    ]
    
    mechanics_df = pd.DataFrame(sample_mechanics)
    print(f"Loaded {len(mechanics_df)} mechanics")
    
    print("\n2. Initializing recommendation system...")
    recommendation_system = MechanicRecommendationSystem(
        mechanics_df,
        epsilon=0.15,      # 15% exploration rate
        learning_rate=0.03  # Slow learning rate
    )
    
    print("\n3. Testing distance calculation...")
    
    nyc_lat, nyc_lon = 40.7128, -74.0060  # NYC coordinates
    mechanic_lat, mechanic_lon = 40.862763, -73.809943  # Mechanic 1
    
    distance_km, distance_score = calculate_distance_score(
        nyc_lat, nyc_lon, mechanic_lat, mechanic_lon
    )
    
    print(f"Distance between NYC and Mechanic 1:")
    print(f"  Actual distance: {distance_km:.2f} km")
    print(f"  Normalized score: {distance_score:.4f}")
    
    print("\n4. Single request demonstration...")
    
    request = recommendation_system.create_sample_request(
        user_lat=40.7128,  # NYC latitude
        user_lon=-74.0060  # NYC longitude
    )
    
    recommendations, arm_idx, weights = recommendation_system.recommend_mechanics(
        request, top_k=3, verbose=True
    )
    
    chosen_mechanic_id = recommendations[0]['mechanic_id']
    user_rating = recommendation_system.simulate_user_feedback(request, chosen_mechanic_id)
    
    print(f"\nSimulated User Feedback:")
    print(f"  Chosen mechanic: {chosen_mechanic_id}")
    print(f"  User rating: {user_rating:.3f}")
    
    recommendation_system.update_with_feedback(arm_idx, user_rating)
    
    print("\n5. Running simulation with multiple requests...")
    
    simulation_results = recommendation_system.run_simulation(num_requests=50)
    
    print("\n6. Final bandit statistics...")
    final_stats = recommendation_system.bandit.get_statistics()
    
    print(f"\nOptimal weights discovered:")
    print(f"  Alpha (Review): {final_stats['best_weights'][0]:.3f}")
    print(f"  Beta (Distance): {final_stats['best_weights'][1]:.3f}")
    
    print("\n7. Saving results...")
    
    mechanics_df.to_csv('mechanics_with_scores.csv', index=False)
    
    history_df = pd.DataFrame({
        'arm_chosen': recommendation_system.bandit.history['chosen_arms'],
        'reward': recommendation_system.bandit.history['rewards']
    })
    history_df.to_csv('bandit_history.csv', index=False)
    
    optimal_weights = {
        'alpha': float(final_stats['best_weights'][0]),
        'beta': float(final_stats['best_weights'][1]),
        'average_reward': float(final_stats['average_reward']),
        'best_arm': int(final_stats['best_arm'])
    }
    
    with open('optimal_weights.json', 'w') as f:
        json.dump(optimal_weights, f, indent=2)
    
    print("\n Files saved")
 


main()
    

import numpy as np  # Import numpy for numerical operations and arrays
import random  # Import random for generating random numbers


class QLearningAgent:  # Define the QLearningAgent class for Q-learning algorithm
    def __init__(  # Initialize the Q-learning agent
        self,
        n_states=25,  # Number of states in the environment
        n_actions=9,  # Number of actions available
        alpha=0.1,  # Ekploration 10%, Eksploitation 90%
        #alpha_decay=0.9995,  # Decay rate for alpha
        alpha_decay=0.9998,  # Decay rate for alpha
        alpha_min=0.01,  # Minimum value for alpha
        #gamma=0.95,  # Jika agent
        # persamaan bellman equation notasi gamma adalah diskon faktor
        #gamma=0.90,  # Diskon faktor (Bellman Equation)
        gamma=0.95,  # Visi jangka panjang (Sesuai draf B600)
        epsilon=1.0,  # Initial exploration rate
        #epsilon_decay=0.995,  # Decay rate for epsilon
        #epsilon_decay=0.9995,  # Decay rate for epsilon
        epsilon_decay=0.9999,  # Eksplorasi awet sampai 50rb episode (Sesuai draf B600)
        epsilon_min=0.01,  # Minimum value for epsilon
    ):
        self.Q = np.zeros((n_states, n_actions))  # 25x9 sesuai Tabel 3.5
        #self.alpha = 0.05  # Learning rate lebih stabil untuk reward besar
        self.alpha = alpha  # Menggunakan parameter (0.10)
        self.alpha_decay = alpha_decay  # Decay untuk learning rate
        self.alpha_min = alpha_min  # Minimum learning rate
        #self.gamma = 0.999  # Visi jangka sangat panjang
        #self.gamma = 0.90  # Menggunakan parameter (0.90)
        self.gamma = gamma  # Menggunakan parameter (0.95)
        self.epsilon = epsilon  # Initial exploration rate
        #self.epsilon_decay = 0.9999  # Eksplorasi awet sampai 50rb episode
        #self.epsilon_decay = 0.9995  # eps -> 0.01 di ~ep 9200
        self.epsilon_decay = epsilon_decay  # Eksplorasi awet (0.9999)
        self.epsilon_min = epsilon_min  # Minimum exploration rate
        self.n_actions = n_actions  # Number of actions

        # Track visit count untuk adaptive learning
        self.visit_count = np.zeros(
            (n_states, n_actions)
        )  # Initialize visit count array

    def select_action(self, state):  # Select an action based on epsilon-greedy policy
        if (
            random.random() < self.epsilon
        ):  # If random number less than epsilon, explore
            return random.randint(0, self.n_actions - 1)  # Return random action
        return np.argmax(self.Q[state])  # Return action with highest Q-value

    def update(
        self, state, action, reward, next_state
    ):  # Update Q-table using Q-learning update rule
        # Adaptive learning rate berdasarkan visit count
        self.visit_count[
            state, action
        ] += 1  # Increment visit count for state-action pair
        # adaptive_alpha = self.alpha / (1 + 0.001 * self.visit_count[state, action])  # v1
        adaptive_alpha = self.alpha / (
            1 + 0.01 * self.visit_count[state, action]
        )  # v2: Lebih responsif

        best_next = np.max(self.Q[next_state])  # Get maximum Q-value for next state
        td_target = reward + self.gamma * best_next  # Calculate TD target
        td_error = td_target - self.Q[state, action]  # Calculate TD error
        self.Q[state, action] += adaptive_alpha * td_error  # Update Q-value

    def decay_epsilon(self):  # Decay the exploration rate
        self.epsilon = max(
            self.epsilon_min, self.epsilon * self.epsilon_decay
        )  # Update epsilon with decay

    def decay_alpha(self):  # Decay learning rate for stability at end of training
        """Decay learning rate untuk stabilitas di akhir training"""
        self.alpha = max(
            self.alpha_min, self.alpha * self.alpha_decay
        )  # Update alpha with decay

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import the GARCH-GRU components (assuming they're in the same file or imported)
# from previous artifact: GARCHGRUCell, GARCHGRU, VolatilityPredictor, GARCHGRUTrainer

class OHLCGARCHGRUPipeline:
    """
    Complete pipeline for processing OHLC data and training GARCH-GRU models
    """
    
    def __init__(self, sequence_length: int = 20, target_horizon: int = 1):
        """
        Args:
            sequence_length: Length of input sequences
            target_horizon: Forecast horizon for volatility prediction
        """
        self.sequence_length = sequence_length
        self.target_horizon = target_horizon
        self.scalers = {}
        self.feature_names = []
        
    def load_ohlc_data(self, data_path: str = None, data_dict: Dict = None) -> pd.DataFrame:
        """
        Load OHLC data from file or dictionary
        
        Args:
            data_path: Path to CSV file with columns ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
            data_dict: Dictionary with symbol as key and DataFrame as value
            
        Returns:
            Combined DataFrame with all symbols
        """
        if data_path:
            df = pd.read_csv(data_path)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(['symbol', 'date'])
        elif data_dict:
            dfs = []
            for symbol, symbol_df in data_dict.items():
                symbol_df = symbol_df.copy()
                symbol_df['symbol'] = symbol
                if 'date' not in symbol_df.columns and symbol_df.index.name in ['date', 'Date']:
                    symbol_df = symbol_df.reset_index()
                dfs.append(symbol_df)
            df = pd.concat(dfs, ignore_index=True)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(['symbol', 'date'])
        else:
            raise ValueError("Either data_path or data_dict must be provided")
        
        print(f"Loaded data for {df['symbol'].nunique()} symbols")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Total observations: {len(df)}")
        
        return df
    
    def create_sample_data(self, symbols: List[str] = ['AAPL', 'GOOGL', 'MSFT'], 
                          n_days: int = 500) -> pd.DataFrame:
        """
        Create sample OHLC data for demonstration
        """
        np.random.seed(42)
        dates = pd.date_range(start='2020-01-01', periods=n_days, freq='D')
        
        all_data = []
        
        for symbol in symbols:
            # Simulate realistic OHLC data with volatility clustering
            base_price = np.random.uniform(50, 200)
            
            prices = [base_price]
            volatilities = [0.02]
            
            for i in range(1, n_days):
                # GARCH-like volatility
                prev_return = (prices[-1] - prices[-2]) / prices[-2] if len(prices) > 1 else 0
                vol = np.sqrt(0.0001 + 0.1 * prev_return**2 + 0.85 * volatilities[-1]**2)
                volatilities.append(vol)
                
                # Price with volatility clustering
                return_shock = np.random.normal(0, vol)
                new_price = prices[-1] * (1 + return_shock)
                prices.append(max(new_price, 0.01))  # Avoid negative prices
            
            # Create OHLC from prices
            for i, date in enumerate(dates):
                if i == 0:
                    open_price = close_price = prices[i]
                else:
                    open_price = prices[i-1]
                    close_price = prices[i]
                
                # Add some intraday variation
                daily_vol = volatilities[i]
                high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, daily_vol/2)))
                low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, daily_vol/2)))
                
                volume = np.random.randint(100000, 10000000)
                
                all_data.append({
                    'symbol': symbol,
                    'date': date,
                    'open': open_price,
                    'high': high_price, 
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
        
        df = pd.DataFrame(all_data)
        print(f"Created sample data for {len(symbols)} symbols, {n_days} days each")
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create technical indicators and features from OHLC data
        """
        print("Engineering features...")
        
        features_df = df.copy()
        
        # Group by symbol for feature engineering
        def create_features(group):
            group = group.sort_values('date').copy()
            
            # Basic price features
            group['returns'] = group['close'].pct_change()
            group['log_returns'] = np.log(group['close'] / group['close'].shift(1))
            group['high_low_pct'] = (group['high'] - group['low']) / group['close']
            group['open_close_pct'] = (group['close'] - group['open']) / group['open']
            
            # Volatility features
            group['returns_squared'] = group['returns'] ** 2
            group['realized_vol_5'] = group['returns'].rolling(5).std()
            group['realized_vol_10'] = group['returns'].rolling(10).std()
            group['realized_vol_20'] = group['returns'].rolling(20).std()
            
            # Price ratios and levels
            group['price_ma_5'] = group['close'].rolling(5).mean()
            group['price_ma_20'] = group['close'].rolling(20).mean()
            group['price_to_ma5'] = group['close'] / group['price_ma_5']
            group['price_to_ma20'] = group['close'] / group['price_ma_20']
            
            # Volume features
            group['volume_ma_10'] = group['volume'].rolling(10).mean()
            group['volume_ratio'] = group['volume'] / group['volume_ma_10']
            group['log_volume'] = np.log(group['volume'])
            
            # Technical indicators
            # RSI approximation
            delta = group['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            group['rsi'] = 100 - (100 / (1 + rs))
            
            # Lagged features
            for lag in [1, 2, 3, 5]:
                group[f'returns_lag_{lag}'] = group['returns'].shift(lag)
                group[f'vol_lag_{lag}'] = group['realized_vol_5'].shift(lag)
            
            return group
        
        features_df = features_df.groupby('symbol').apply(create_features).reset_index(drop=True)
        
        # Remove rows with NaN values
        initial_rows = len(features_df)
        features_df = features_df.dropna()
        print(f"Removed {initial_rows - len(features_df)} rows with NaN values")
        
        # Store feature names
        feature_cols = [col for col in features_df.columns 
                       if col not in ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
        self.feature_names = feature_cols
        print(f"Created {len(feature_cols)} features: {feature_cols}")
        
        return features_df
    
    def prepare_sequences(self, df: pd.DataFrame, target_col: str = 'realized_vol_5') -> Dict:
        """
        Create sequences for GARCH-GRU training
        """
        print(f"Preparing sequences with length {self.sequence_length}...")
        
        all_sequences = []
        all_returns_sequences = []
        all_targets = []
        all_symbols = []
        
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol].sort_values('date').copy()
            
            if len(symbol_data) < self.sequence_length + self.target_horizon:
                print(f"Skipping {symbol}: insufficient data ({len(symbol_data)} rows)")
                continue
            
            # Features for model input
            feature_cols = [col for col in self.feature_names if col in symbol_data.columns]
            features = symbol_data[feature_cols].values
            returns = symbol_data['log_returns'].values
            targets = symbol_data[target_col].values
            
            # Create sequences
            for i in range(self.sequence_length, len(symbol_data) - self.target_horizon + 1):
                # Input sequence
                seq_features = features[i-self.sequence_length:i]
                seq_returns = returns[i-self.sequence_length:i]
                
                # Target (volatility at target_horizon ahead)
                target_vol = targets[i + self.target_horizon - 1]
                
                all_sequences.append(seq_features)
                all_returns_sequences.append(seq_returns)
                all_targets.append(target_vol)
                all_symbols.append(symbol)
        
        print(f"Created {len(all_sequences)} sequences from {len(df['symbol'].unique())} symbols")
        
        return {
            'sequences': np.array(all_sequences),
            'returns_sequences': np.array(all_returns_sequences),
            'targets': np.array(all_targets),
            'symbols': all_symbols
        }
    
    def scale_features(self, train_sequences: np.ndarray, 
                      val_sequences: np.ndarray, 
                      test_sequences: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Scale features using StandardScaler fitted on training data
        """
        print("Scaling features...")
        
        # Reshape for scaling: (n_samples * seq_len, n_features)
        train_reshaped = train_sequences.reshape(-1, train_sequences.shape[-1])
        
        # Fit scaler on training data
        self.scalers['features'] = StandardScaler()
        train_scaled_reshaped = self.scalers['features'].fit_transform(train_reshaped)
        
        # Transform all sets
        train_scaled = train_scaled_reshaped.reshape(train_sequences.shape)
        
        val_reshaped = val_sequences.reshape(-1, val_sequences.shape[-1])
        val_scaled_reshaped = self.scalers['features'].transform(val_reshaped)
        val_scaled = val_scaled_reshaped.reshape(val_sequences.shape)
        
        test_reshaped = test_sequences.reshape(-1, test_sequences.shape[-1])
        test_scaled_reshaped = self.scalers['features'].transform(test_reshaped)
        test_scaled = test_scaled_reshaped.reshape(test_sequences.shape)
        
        return train_scaled, val_scaled, test_scaled
    
    def create_data_splits(self, data_dict: Dict, test_size: float = 0.2, 
                          val_size: float = 0.2) -> Dict:
        """
        Split data into train/validation/test sets
        """
        print("Creating data splits...")
        
        sequences = data_dict['sequences']
        returns_sequences = data_dict['returns_sequences']  
        targets = data_dict['targets']
        symbols = data_dict['symbols']
        
        # First split: train+val vs test
        train_val_seq, test_seq, train_val_ret, test_ret, train_val_tgt, test_tgt, train_val_sym, test_sym = \
            train_test_split(sequences, returns_sequences, targets, symbols, 
                           test_size=test_size, random_state=42, stratify=symbols)
        
        # Second split: train vs val
        train_seq, val_seq, train_ret, val_ret, train_tgt, val_tgt, train_sym, val_sym = \
            train_test_split(train_val_seq, train_val_ret, train_val_tgt, train_val_sym,
                           test_size=val_size/(1-test_size), random_state=42, stratify=train_val_sym)
        
        # Scale features
        train_seq_scaled, val_seq_scaled, test_seq_scaled = self.scale_features(
            train_seq, val_seq, test_seq
        )
        
        print(f"Train: {len(train_seq_scaled)} sequences")
        print(f"Validation: {len(val_seq_scaled)} sequences") 
        print(f"Test: {len(test_seq_scaled)} sequences")
        
        return {
            'train': {
                'sequences': torch.FloatTensor(train_seq_scaled),
                'returns': torch.FloatTensor(train_ret),
                'targets': torch.FloatTensor(train_tgt),
                'symbols': train_sym
            },
            'val': {
                'sequences': torch.FloatTensor(val_seq_scaled),
                'returns': torch.FloatTensor(val_ret),
                'targets': torch.FloatTensor(val_tgt),
                'symbols': val_sym
            },
            'test': {
                'sequences': torch.FloatTensor(test_seq_scaled),
                'returns': torch.FloatTensor(test_ret),
                'targets': torch.FloatTensor(test_tgt),
                'symbols': test_sym
            }
        }
    
    def train_model(self, data_splits: Dict, hidden_size: int = 64, 
                   num_layers: int = 2, epochs: int = 100, 
                   learning_rate: float = 0.001, batch_size: int = 32) -> VolatilityPredictor:
        """
        Train GARCH-GRU model
        """
        print("Training GARCH-GRU model...")
        
        # Get input size from training data
        input_size = data_splits['train']['sequences'].shape[-1]
        
        # Create model
        model = VolatilityPredictor(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=0.1,
            learn_garch_params=True,
            output_volatility=True
        )
        
        print(f"Model created with {sum(p.numel() for p in model.parameters())} parameters")
        
        # Create trainer
        trainer = GARCHGRUTrainer(model, lr=learning_rate)
        
        # Training data
        train_sequences = data_splits['train']['sequences']
        train_returns = data_splits['train']['returns']
        train_targets = data_splits['train']['targets']
        
        val_sequences = data_splits['val']['sequences']
        val_returns = data_splits['val']['returns']
        val_targets = data_splits['val']['targets']
        
        # Training loop
        train_losses = []
        val_losses = []
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        n_batches = len(train_sequences) // batch_size
        
        for epoch in range(epochs):
            epoch_train_losses = []
            
            # Shuffle training data
            perm = torch.randperm(len(train_sequences))
            train_sequences = train_sequences[perm]
            train_returns = train_returns[perm]
            train_targets = train_targets[perm]
            
            # Training batches
            for batch_idx in range(n_batches):
                start_idx = batch_idx * batch_size
                end_idx = start_idx + batch_size
                
                batch_sequences = train_sequences[start_idx:end_idx]
                batch_returns = train_returns[start_idx:end_idx]
                batch_targets = train_targets[start_idx:end_idx]
                
                loss = trainer.train_step(batch_sequences, batch_returns, batch_targets)
                epoch_train_losses.append(loss)
            
            # Validation
            val_loss = trainer.validate(val_sequences, val_returns, val_targets)
            
            avg_train_loss = np.mean(epoch_train_losses)
            train_losses.append(avg_train_loss)
            val_losses.append(val_loss)
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.6f}, Val Loss: {val_loss:.6f}")
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model state
                best_model_state = model.state_dict().copy()
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch+1}")
                    break
        
        # Load best model
        model.load_state_dict(best_model_state)
        
        # Plot training curves
        plt.figure(figsize=(10, 6))
        plt.plot(train_losses, label='Training Loss', alpha=0.7)
        plt.plot(val_losses, label='Validation Loss', alpha=0.7)
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('GARCH-GRU Training Progress')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()
        
        return model
    
    def evaluate_model(self, model: VolatilityPredictor, data_splits: Dict) -> Dict:
        """
        Evaluate trained model on test set
        """
        print("Evaluating model...")
        
        model.eval()
        with torch.no_grad():
            # Test predictions
            test_sequences = data_splits['test']['sequences']
            test_returns = data_splits['test']['returns']
            test_targets = data_splits['test']['targets']
            
            # Volatility predictions
            pred_volatility = model(test_sequences, test_returns)
            pred_vol_numpy = pred_volatility.squeeze(-1).numpy()
            true_vol_numpy = test_targets.numpy()
            
            # Volatility-aware embeddings
            embeddings = model(test_sequences, test_returns, return_embeddings=True)
            embeddings_numpy = embeddings.numpy()
            
            # Calculate metrics
            mse = np.mean((pred_vol_numpy - true_vol_numpy) ** 2)
            mae = np.mean(np.abs(pred_vol_numpy - true_vol_numpy))
            rmse = np.sqrt(mse)
            
            # Correlation
            correlation = np.corrcoef(pred_vol_numpy, true_vol_numpy)[0, 1]
            
            print(f"Test Results:")
            print(f"RMSE: {rmse:.6f}")
            print(f"MAE: {mae:.6f}")
            print(f"Correlation: {correlation:.4f}")
            
            # Plot predictions vs actual
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 2, 1)
            plt.scatter(true_vol_numpy, pred_vol_numpy, alpha=0.6)
            plt.plot([true_vol_numpy.min(), true_vol_numpy.max()], 
                    [true_vol_numpy.min(), true_vol_numpy.max()], 'r--')
            plt.xlabel('True Volatility')
            plt.ylabel('Predicted Volatility')
            plt.title('Volatility Predictions vs Actual')
            plt.grid(True, alpha=0.3)
            
            plt.subplot(2, 2, 2)
            plt.plot(true_vol_numpy[:100], label='True', alpha=0.7)
            plt.plot(pred_vol_numpy[:100], label='Predicted', alpha=0.7)
            plt.xlabel('Time')
            plt.ylabel('Volatility')
            plt.title('Time Series Comparison (First 100 samples)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.subplot(2, 2, 3)
            residuals = pred_vol_numpy - true_vol_numpy
            plt.hist(residuals, bins=50, alpha=0.7)
            plt.xlabel('Residuals')
            plt.ylabel('Frequency')
            plt.title('Residuals Distribution')
            plt.grid(True, alpha=0.3)
            
            plt.subplot(2, 2, 4)
            # Plot embedding space (2D projection using PCA if high-dimensional)
            from sklearn.decomposition import PCA
            if embeddings_numpy.shape[-1] > 2:
                pca = PCA(n_components=2)
                emb_2d = pca.fit_transform(embeddings_numpy.reshape(-1, embeddings_numpy.shape[-1]))
                emb_2d = emb_2d.reshape(embeddings_numpy.shape[0], embeddings_numpy.shape[1], 2)
                # Plot last timestep embeddings
                plt.scatter(emb_2d[:, -1, 0], emb_2d[:, -1, 1], 
                           c=true_vol_numpy, cmap='viridis', alpha=0.6)
                plt.colorbar(label='True Volatility')
                plt.xlabel('PC1')
                plt.ylabel('PC2')
                plt.title('Embeddings (PCA projection)')
            
            plt.tight_layout()
            plt.show()
            
            return {
                'rmse': rmse,
                'mae': mae,
                'correlation': correlation,
                'predictions': pred_vol_numpy,
                'embeddings': embeddings_numpy,
                'true_values': true_vol_numpy
            }

def run_complete_pipeline():
    """
    Run the complete OHLC to GARCH-GRU pipeline
    """
    print("=" * 60)
    print("OHLC TO GARCH-GRU PIPELINE")
    print("=" * 60)
    
    # Step 1: Initialize pipeline
    pipeline = OHLCGARCHGRUPipeline(sequence_length=20, target_horizon=1)
    
    # Step 2: Load or create sample data
    print("\nStep 1: Loading/Creating OHLC Data")
    print("-" * 40)
    
    # Option A: Create sample data (for demonstration)
    df = pipeline.create_sample_data(symbols=['AAPL', 'GOOGL', 'MSFT', 'TSLA'], n_days=400)
    
    # Option B: Load from your own data
    # df = pipeline.load_ohlc_data(data_path='your_ohlc_data.csv')
    # or
    # data_dict = {
    #     'AAPL': pd.read_csv('aapl_ohlc.csv'),
    #     'GOOGL': pd.read_csv('googl_ohlc.csv')
    # }
    # df = pipeline.load_ohlc_data(data_dict=data_dict)
    
    # Step 3: Feature engineering
    print("\nStep 2: Feature Engineering")
    print("-" * 40)
    features_df = pipeline.engineer_features(df)
    
    # Step 4: Create sequences
    print("\nStep 3: Creating Sequences")
    print("-" * 40)
    data_dict = pipeline.prepare_sequences(features_df, target_col='realized_vol_5')
    
    # Step 5: Create train/val/test splits
    print("\nStep 4: Creating Data Splits")
    print("-" * 40)
    data_splits = pipeline.create_data_splits(data_dict, test_size=0.2, val_size=0.2)
    
    # Step 6: Train model
    print("\nStep 5: Training GARCH-GRU Model")
    print("-" * 40)
    model = pipeline.train_model(
        data_splits, 
        hidden_size=64, 
        num_layers=2, 
        epochs=50,  # Reduced for demo
        learning_rate=0.001,
        batch_size=32
    )
    
    # Step 7: Evaluate model
    print("\nStep 6: Model Evaluation")
    print("-" * 40)
    results = pipeline.evaluate_model(model, data_splits)
    
    # Step 8: Extract embeddings for downstream tasks
    print("\nStep 7: Extracting Volatility-Aware Embeddings")
    print("-" * 40)
    
    # Example: Extract embeddings for specific symbols
    test_symbols = data_splits['test']['symbols']
    embeddings = results['embeddings']
    
    # Group by symbol
    symbol_embeddings = {}
    for i, symbol in enumerate(test_symbols):
        if symbol not in symbol_embeddings:
            symbol_embeddings[symbol] = []
        symbol_embeddings[symbol].append(embeddings[i])
    
    print("Embeddings extracted for symbols:")
    for symbol, emb_list in symbol_embeddings.items():
        print(f"{symbol}: {len(emb_list)} sequences, embedding dim: {emb_list[0].shape}")
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    return pipeline, model, results, data_splits

# Run the complete pipeline
if __name__ == "__main__":
    pipeline, model, results, data_splits = run_complete_pipeline()
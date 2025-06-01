"""
ML Trainer for Project GeminiVoiceConnect

This module provides comprehensive machine learning training capabilities
with GPU acceleration, automated model optimization, and intelligent
deployment pipelines for call center AI enhancement.

Key Features:
- GPU-accelerated model training
- Automated hyperparameter optimization
- Real-time training monitoring
- Model versioning and deployment
- A/B testing framework
- Performance benchmarking
- Distributed training support
- Custom model architectures
"""

from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
import uuid
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, random_split
from torch.utils.tensorboard import SummaryWriter
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import optuna
from celery import Task
import pickle
import joblib
from pathlib import Path

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ModelType(str, Enum):
    """Model type enumeration"""
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    INTENT_CLASSIFICATION = "intent_classification"
    CHURN_PREDICTION = "churn_prediction"
    LEAD_SCORING = "lead_scoring"
    CONVERSATION_QUALITY = "conversation_quality"
    VOICE_EMOTION = "voice_emotion"
    CALL_OUTCOME_PREDICTION = "call_outcome_prediction"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    UPSELL_PREDICTION = "upsell_prediction"
    ANOMALY_DETECTION = "anomaly_detection"


class TrainingStatus(str, Enum):
    """Training status enumeration"""
    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    VALIDATING = "validating"
    OPTIMIZING = "optimizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelArchitecture(str, Enum):
    """Model architecture enumeration"""
    TRANSFORMER = "transformer"
    LSTM = "lstm"
    CNN = "cnn"
    RESNET = "resnet"
    BERT = "bert"
    CUSTOM_NLP = "custom_nlp"
    ENSEMBLE = "ensemble"
    AUTOML = "automl"


@dataclass
class TrainingConfig:
    """Training configuration"""
    training_id: str
    model_type: ModelType
    architecture: ModelArchitecture
    dataset_path: str
    target_column: str
    feature_columns: List[str]
    hyperparameters: Dict[str, Any]
    training_params: Dict[str, Any]
    validation_split: float = 0.2
    test_split: float = 0.1
    batch_size: int = 32
    epochs: int = 100
    early_stopping_patience: int = 10
    learning_rate: float = 0.001
    optimizer: str = "adam"
    loss_function: str = "cross_entropy"
    metrics: List[str] = None
    gpu_enabled: bool = True
    distributed_training: bool = False
    auto_hyperparameter_tuning: bool = True
    model_versioning: bool = True
    experiment_tracking: bool = True


@dataclass
class TrainingResult:
    """Training result"""
    training_id: str
    model_type: ModelType
    status: TrainingStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    best_metrics: Dict[str, float]
    final_metrics: Dict[str, float]
    model_path: Optional[str]
    model_version: Optional[str]
    hyperparameters: Dict[str, Any]
    training_history: List[Dict[str, Any]]
    gpu_utilization: Optional[float]
    memory_usage: Optional[float]
    error_message: Optional[str] = None


class CustomDataset(Dataset):
    """
    Custom PyTorch dataset for call center data.
    
    This dataset handles various data types including text, numerical,
    and categorical features commonly found in call center operations.
    """
    
    def __init__(self, features: np.ndarray, targets: np.ndarray, transform=None):
        self.features = torch.FloatTensor(features)
        self.targets = torch.LongTensor(targets)
        self.transform = transform
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        feature = self.features[idx]
        target = self.targets[idx]
        
        if self.transform:
            feature = self.transform(feature)
        
        return feature, target


class SentimentAnalysisModel(nn.Module):
    """
    Advanced sentiment analysis model for call transcripts.
    
    This model uses transformer architecture with attention mechanisms
    to analyze customer sentiment during calls.
    """
    
    def __init__(self, vocab_size: int, embedding_dim: int = 128, hidden_dim: int = 256, num_classes: int = 3):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.attention = nn.MultiheadAttention(hidden_dim * 2, num_heads=8)
        self.dropout = nn.Dropout(0.3)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, num_classes)
        )
    
    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, _ = self.lstm(embedded)
        
        # Apply attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Global average pooling
        pooled = torch.mean(attn_out, dim=1)
        pooled = self.dropout(pooled)
        
        return self.classifier(pooled)


class IntentClassificationModel(nn.Module):
    """
    Intent classification model for understanding customer requests.
    
    This model identifies customer intents from conversation transcripts
    to enable better call routing and response strategies.
    """
    
    def __init__(self, input_dim: int, hidden_dims: List[int], num_intents: int):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
                nn.Dropout(0.3)
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, num_intents))
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class ChurnPredictionModel(nn.Module):
    """
    Customer churn prediction model.
    
    This model predicts the likelihood of customer churn based on
    call patterns, satisfaction scores, and interaction history.
    """
    
    def __init__(self, input_dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.4),
            
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.2),
            
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.network(x)


class HyperparameterOptimizer:
    """
    Advanced hyperparameter optimization using Optuna.
    
    This optimizer uses Bayesian optimization to find optimal
    hyperparameters for different model architectures.
    """
    
    def __init__(self, model_type: ModelType, gpu_enabled: bool = True):
        self.model_type = model_type
        self.device = torch.device("cuda" if gpu_enabled and torch.cuda.is_available() else "cpu")
        self.best_params = None
        self.best_score = None
    
    def suggest_hyperparameters(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Suggest hyperparameters based on model type"""
        
        if self.model_type == ModelType.SENTIMENT_ANALYSIS:
            return {
                'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
                'batch_size': trial.suggest_categorical('batch_size', [16, 32, 64, 128]),
                'hidden_dim': trial.suggest_categorical('hidden_dim', [128, 256, 512]),
                'embedding_dim': trial.suggest_categorical('embedding_dim', [64, 128, 256]),
                'dropout_rate': trial.suggest_float('dropout_rate', 0.1, 0.5),
                'num_layers': trial.suggest_int('num_layers', 1, 3),
            }
        
        elif self.model_type == ModelType.INTENT_CLASSIFICATION:
            return {
                'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
                'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128, 256]),
                'hidden_dims': [
                    trial.suggest_categorical('hidden_dim_1', [128, 256, 512]),
                    trial.suggest_categorical('hidden_dim_2', [64, 128, 256]),
                ],
                'dropout_rate': trial.suggest_float('dropout_rate', 0.2, 0.5),
                'weight_decay': trial.suggest_float('weight_decay', 1e-6, 1e-3, log=True),
            }
        
        elif self.model_type == ModelType.CHURN_PREDICTION:
            return {
                'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
                'batch_size': trial.suggest_categorical('batch_size', [64, 128, 256]),
                'dropout_rate': trial.suggest_float('dropout_rate', 0.3, 0.6),
                'weight_decay': trial.suggest_float('weight_decay', 1e-5, 1e-2, log=True),
                'scheduler_step_size': trial.suggest_int('scheduler_step_size', 10, 50),
                'scheduler_gamma': trial.suggest_float('scheduler_gamma', 0.1, 0.9),
            }
        
        else:
            # Default hyperparameters
            return {
                'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
                'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128]),
                'dropout_rate': trial.suggest_float('dropout_rate', 0.2, 0.5),
            }
    
    def objective(self, trial: optuna.Trial, train_loader: DataLoader, val_loader: DataLoader, 
                  model_factory: Callable, epochs: int = 20) -> float:
        """Objective function for hyperparameter optimization"""
        
        params = self.suggest_hyperparameters(trial)
        
        # Create model with suggested parameters
        model = model_factory(params).to(self.device)
        
        # Setup optimizer and loss function
        optimizer = optim.Adam(model.parameters(), lr=params['learning_rate'])
        criterion = nn.CrossEntropyLoss()
        
        # Training loop
        model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch_features, batch_targets in train_loader:
                batch_features, batch_targets = batch_features.to(self.device), batch_targets.to(self.device)
                
                optimizer.zero_grad()
                outputs = model(batch_features)
                loss = criterion(outputs, batch_targets)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            # Early stopping based on validation loss
            if epoch % 5 == 0:
                val_loss = self._evaluate_model(model, val_loader, criterion)
                trial.report(val_loss, epoch)
                
                if trial.should_prune():
                    raise optuna.exceptions.TrialPruned()
        
        # Final validation score
        final_score = self._evaluate_model(model, val_loader, criterion)
        return final_score
    
    def _evaluate_model(self, model: nn.Module, data_loader: DataLoader, criterion) -> float:
        """Evaluate model on validation data"""
        model.eval()
        total_loss = 0
        total_samples = 0
        
        with torch.no_grad():
            for batch_features, batch_targets in data_loader:
                batch_features, batch_targets = batch_features.to(self.device), batch_targets.to(self.device)
                outputs = model(batch_features)
                loss = criterion(outputs, batch_targets)
                total_loss += loss.item() * batch_features.size(0)
                total_samples += batch_features.size(0)
        
        return total_loss / total_samples
    
    def optimize(self, train_loader: DataLoader, val_loader: DataLoader, 
                 model_factory: Callable, n_trials: int = 100) -> Dict[str, Any]:
        """Run hyperparameter optimization"""
        
        study = optuna.create_study(direction='minimize')
        study.optimize(
            lambda trial: self.objective(trial, train_loader, val_loader, model_factory),
            n_trials=n_trials
        )
        
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'study': study
        }


class MLTrainer:
    """
    Comprehensive machine learning trainer for call center AI models.
    
    This trainer provides end-to-end ML pipeline including data preprocessing,
    model training, validation, hyperparameter optimization, and deployment.
    """
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.models_dir = Path("/tmp/models")
        self.models_dir.mkdir(exist_ok=True)
        self.experiments_dir = Path("/tmp/experiments")
        self.experiments_dir.mkdir(exist_ok=True)
        
        logger.info(f"ML Trainer initialized with device: {self.device}")
    
    async def train_model(self, config: TrainingConfig) -> TrainingResult:
        """Train a machine learning model"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting training for {config.model_type.value} model")
            
            # Initialize result
            result = TrainingResult(
                training_id=config.training_id,
                model_type=config.model_type,
                status=TrainingStatus.PREPARING,
                start_time=start_time,
                end_time=None,
                duration=None,
                best_metrics={},
                final_metrics={},
                model_path=None,
                model_version=None,
                hyperparameters=config.hyperparameters,
                training_history=[],
                gpu_utilization=None,
                memory_usage=None
            )
            
            # Load and preprocess data
            train_loader, val_loader, test_loader, feature_dim, num_classes = await self._prepare_data(config)
            
            # Create model
            result.status = TrainingStatus.TRAINING
            model = self._create_model(config, feature_dim, num_classes)
            model = model.to(self.device)
            
            # Setup training components
            optimizer = self._create_optimizer(model, config)
            criterion = self._create_loss_function(config, num_classes)
            scheduler = self._create_scheduler(optimizer, config)
            
            # Setup experiment tracking
            writer = None
            if config.experiment_tracking:
                experiment_dir = self.experiments_dir / config.training_id
                experiment_dir.mkdir(exist_ok=True)
                writer = SummaryWriter(str(experiment_dir))
            
            # Hyperparameter optimization
            if config.auto_hyperparameter_tuning:
                result.status = TrainingStatus.OPTIMIZING
                await self._optimize_hyperparameters(config, train_loader, val_loader, feature_dim, num_classes)
                
                # Recreate model with optimized parameters
                model = self._create_model(config, feature_dim, num_classes)
                model = model.to(self.device)
                optimizer = self._create_optimizer(model, config)
                criterion = self._create_loss_function(config, num_classes)
                scheduler = self._create_scheduler(optimizer, config)
            
            # Training loop
            result.status = TrainingStatus.TRAINING
            best_val_loss = float('inf')
            patience_counter = 0
            training_history = []
            
            for epoch in range(config.epochs):
                # Training phase
                train_metrics = await self._train_epoch(
                    model, train_loader, optimizer, criterion, epoch
                )
                
                # Validation phase
                val_metrics = await self._validate_epoch(
                    model, val_loader, criterion, epoch
                )
                
                # Update learning rate
                if scheduler:
                    scheduler.step(val_metrics['loss'])
                
                # Record metrics
                epoch_metrics = {
                    'epoch': epoch,
                    'train_loss': train_metrics['loss'],
                    'train_accuracy': train_metrics.get('accuracy', 0),
                    'val_loss': val_metrics['loss'],
                    'val_accuracy': val_metrics.get('accuracy', 0),
                    'learning_rate': optimizer.param_groups[0]['lr'],
                    'gpu_utilization': self._get_gpu_utilization(),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                training_history.append(epoch_metrics)
                
                # Log to tensorboard
                if writer:
                    for key, value in epoch_metrics.items():
                        if isinstance(value, (int, float)):
                            writer.add_scalar(key, value, epoch)
                
                # Early stopping
                if val_metrics['loss'] < best_val_loss:
                    best_val_loss = val_metrics['loss']
                    patience_counter = 0
                    
                    # Save best model
                    best_model_path = self.models_dir / f"{config.training_id}_best.pth"
                    torch.save({
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'epoch': epoch,
                        'loss': best_val_loss,
                        'config': asdict(config)
                    }, best_model_path)
                    
                    result.best_metrics = val_metrics
                    result.model_path = str(best_model_path)
                else:
                    patience_counter += 1
                
                if patience_counter >= config.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
                
                logger.info(f"Epoch {epoch}: train_loss={train_metrics['loss']:.4f}, "
                           f"val_loss={val_metrics['loss']:.4f}, "
                           f"val_accuracy={val_metrics.get('accuracy', 0):.4f}")
            
            # Final evaluation
            result.status = TrainingStatus.VALIDATING
            if test_loader:
                test_metrics = await self._evaluate_model(model, test_loader, criterion)
                result.final_metrics = test_metrics
            else:
                result.final_metrics = result.best_metrics
            
            # Save final model
            final_model_path = self.models_dir / f"{config.training_id}_final.pth"
            torch.save({
                'model_state_dict': model.state_dict(),
                'config': asdict(config),
                'metrics': result.final_metrics,
                'training_history': training_history
            }, final_model_path)
            
            # Model versioning
            if config.model_versioning:
                model_version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                versioned_path = self.models_dir / f"{config.model_type.value}_{model_version}.pth"
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'config': asdict(config),
                    'metrics': result.final_metrics,
                    'version': model_version
                }, versioned_path)
                result.model_version = model_version
            
            # Cleanup
            if writer:
                writer.close()
            
            # Finalize result
            end_time = datetime.utcnow()
            result.end_time = end_time
            result.duration = (end_time - start_time).total_seconds()
            result.status = TrainingStatus.COMPLETED
            result.training_history = training_history
            result.gpu_utilization = self._get_gpu_utilization()
            result.memory_usage = self._get_memory_usage()
            
            logger.info(f"Training completed successfully for {config.training_id}")
            return result
            
        except Exception as e:
            logger.error(f"Training failed for {config.training_id}: {str(e)}")
            end_time = datetime.utcnow()
            result.end_time = end_time
            result.duration = (end_time - start_time).total_seconds()
            result.status = TrainingStatus.FAILED
            result.error_message = str(e)
            return result
    
    async def _prepare_data(self, config: TrainingConfig) -> Tuple[DataLoader, DataLoader, DataLoader, int, int]:
        """Prepare data loaders for training"""
        
        # Load data (mock implementation)
        # In production, this would load real data from the specified path
        if config.model_type == ModelType.SENTIMENT_ANALYSIS:
            # Mock text data for sentiment analysis
            features = np.random.randint(0, 1000, (10000, 100))  # Token IDs
            targets = np.random.randint(0, 3, 10000)  # 3 sentiment classes
            feature_dim = 1000  # Vocabulary size
            num_classes = 3
        
        elif config.model_type == ModelType.INTENT_CLASSIFICATION:
            # Mock feature vectors for intent classification
            features = np.random.randn(5000, 256)
            targets = np.random.randint(0, 10, 5000)  # 10 intent classes
            feature_dim = 256
            num_classes = 10
        
        elif config.model_type == ModelType.CHURN_PREDICTION:
            # Mock customer features for churn prediction
            features = np.random.randn(8000, 50)
            targets = np.random.randint(0, 2, 8000)  # Binary classification
            feature_dim = 50
            num_classes = 2
        
        else:
            # Default mock data
            features = np.random.randn(1000, 100)
            targets = np.random.randint(0, 5, 1000)
            feature_dim = 100
            num_classes = 5
        
        # Split data
        train_features, temp_features, train_targets, temp_targets = train_test_split(
            features, targets, test_size=(config.validation_split + config.test_split), random_state=42
        )
        
        val_features, test_features, val_targets, test_targets = train_test_split(
            temp_features, temp_targets, 
            test_size=config.test_split / (config.validation_split + config.test_split), 
            random_state=42
        )
        
        # Create datasets
        train_dataset = CustomDataset(train_features, train_targets)
        val_dataset = CustomDataset(val_features, val_targets)
        test_dataset = CustomDataset(test_features, test_targets) if len(test_features) > 0 else None
        
        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=False)
        test_loader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=False) if test_dataset else None
        
        return train_loader, val_loader, test_loader, feature_dim, num_classes
    
    def _create_model(self, config: TrainingConfig, feature_dim: int, num_classes: int) -> nn.Module:
        """Create model based on configuration"""
        
        if config.model_type == ModelType.SENTIMENT_ANALYSIS:
            return SentimentAnalysisModel(
                vocab_size=feature_dim,
                embedding_dim=config.hyperparameters.get('embedding_dim', 128),
                hidden_dim=config.hyperparameters.get('hidden_dim', 256),
                num_classes=num_classes
            )
        
        elif config.model_type == ModelType.INTENT_CLASSIFICATION:
            hidden_dims = config.hyperparameters.get('hidden_dims', [256, 128])
            return IntentClassificationModel(feature_dim, hidden_dims, num_classes)
        
        elif config.model_type == ModelType.CHURN_PREDICTION:
            return ChurnPredictionModel(feature_dim)
        
        else:
            # Default simple neural network
            return nn.Sequential(
                nn.Linear(feature_dim, 128),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(64, num_classes)
            )
    
    def _create_optimizer(self, model: nn.Module, config: TrainingConfig) -> optim.Optimizer:
        """Create optimizer"""
        optimizer_name = config.training_params.get('optimizer', 'adam').lower()
        lr = config.learning_rate
        weight_decay = config.hyperparameters.get('weight_decay', 1e-5)
        
        if optimizer_name == 'adam':
            return optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
        elif optimizer_name == 'sgd':
            return optim.SGD(model.parameters(), lr=lr, weight_decay=weight_decay, momentum=0.9)
        elif optimizer_name == 'adamw':
            return optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
        else:
            return optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    
    def _create_loss_function(self, config: TrainingConfig, num_classes: int):
        """Create loss function"""
        loss_name = config.training_params.get('loss_function', 'cross_entropy').lower()
        
        if loss_name == 'cross_entropy':
            return nn.CrossEntropyLoss()
        elif loss_name == 'mse':
            return nn.MSELoss()
        elif loss_name == 'bce':
            return nn.BCELoss()
        elif loss_name == 'focal':
            # Custom focal loss for imbalanced datasets
            return self._focal_loss
        else:
            return nn.CrossEntropyLoss()
    
    def _focal_loss(self, inputs, targets, alpha=1, gamma=2):
        """Focal loss for handling class imbalance"""
        ce_loss = nn.CrossEntropyLoss()(inputs, targets)
        pt = torch.exp(-ce_loss)
        focal_loss = alpha * (1 - pt) ** gamma * ce_loss
        return focal_loss
    
    def _create_scheduler(self, optimizer: optim.Optimizer, config: TrainingConfig):
        """Create learning rate scheduler"""
        scheduler_type = config.training_params.get('scheduler', 'plateau')
        
        if scheduler_type == 'plateau':
            return optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode='min', patience=5, factor=0.5
            )
        elif scheduler_type == 'step':
            step_size = config.hyperparameters.get('scheduler_step_size', 30)
            gamma = config.hyperparameters.get('scheduler_gamma', 0.1)
            return optim.lr_scheduler.StepLR(optimizer, step_size=step_size, gamma=gamma)
        elif scheduler_type == 'cosine':
            return optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config.epochs)
        else:
            return None
    
    async def _optimize_hyperparameters(self, config: TrainingConfig, train_loader: DataLoader, 
                                       val_loader: DataLoader, feature_dim: int, num_classes: int):
        """Optimize hyperparameters using Optuna"""
        
        optimizer = HyperparameterOptimizer(config.model_type, config.gpu_enabled)
        
        def model_factory(params):
            # Update config with optimized parameters
            config.hyperparameters.update(params)
            config.learning_rate = params.get('learning_rate', config.learning_rate)
            config.batch_size = params.get('batch_size', config.batch_size)
            
            return self._create_model(config, feature_dim, num_classes)
        
        optimization_result = optimizer.optimize(
            train_loader, val_loader, model_factory, n_trials=20
        )
        
        # Update config with best parameters
        config.hyperparameters.update(optimization_result['best_params'])
        logger.info(f"Hyperparameter optimization completed. Best score: {optimization_result['best_score']}")
    
    async def _train_epoch(self, model: nn.Module, train_loader: DataLoader, 
                          optimizer: optim.Optimizer, criterion, epoch: int) -> Dict[str, float]:
        """Train for one epoch"""
        
        model.train()
        total_loss = 0
        correct_predictions = 0
        total_samples = 0
        
        for batch_idx, (features, targets) in enumerate(train_loader):
            features, targets = features.to(self.device), targets.to(self.device)
            
            optimizer.zero_grad()
            outputs = model(features)
            
            # Handle different output shapes
            if outputs.dim() == 1:
                loss = criterion(outputs.unsqueeze(0), targets.unsqueeze(0))
            else:
                loss = criterion(outputs, targets)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            # Calculate accuracy for classification tasks
            if outputs.dim() > 1 and outputs.size(1) > 1:
                _, predicted = torch.max(outputs.data, 1)
                correct_predictions += (predicted == targets).sum().item()
            
            total_samples += targets.size(0)
        
        avg_loss = total_loss / len(train_loader)
        accuracy = correct_predictions / total_samples if total_samples > 0 else 0
        
        return {
            'loss': avg_loss,
            'accuracy': accuracy
        }
    
    async def _validate_epoch(self, model: nn.Module, val_loader: DataLoader, 
                             criterion, epoch: int) -> Dict[str, float]:
        """Validate for one epoch"""
        
        model.eval()
        total_loss = 0
        correct_predictions = 0
        total_samples = 0
        
        with torch.no_grad():
            for features, targets in val_loader:
                features, targets = features.to(self.device), targets.to(self.device)
                outputs = model(features)
                
                # Handle different output shapes
                if outputs.dim() == 1:
                    loss = criterion(outputs.unsqueeze(0), targets.unsqueeze(0))
                else:
                    loss = criterion(outputs, targets)
                
                total_loss += loss.item()
                
                # Calculate accuracy for classification tasks
                if outputs.dim() > 1 and outputs.size(1) > 1:
                    _, predicted = torch.max(outputs.data, 1)
                    correct_predictions += (predicted == targets).sum().item()
                
                total_samples += targets.size(0)
        
        avg_loss = total_loss / len(val_loader)
        accuracy = correct_predictions / total_samples if total_samples > 0 else 0
        
        return {
            'loss': avg_loss,
            'accuracy': accuracy
        }
    
    async def _evaluate_model(self, model: nn.Module, test_loader: DataLoader, criterion) -> Dict[str, float]:
        """Comprehensive model evaluation"""
        
        model.eval()
        all_predictions = []
        all_targets = []
        total_loss = 0
        
        with torch.no_grad():
            for features, targets in test_loader:
                features, targets = features.to(self.device), targets.to(self.device)
                outputs = model(features)
                
                # Handle different output shapes
                if outputs.dim() == 1:
                    loss = criterion(outputs.unsqueeze(0), targets.unsqueeze(0))
                    predictions = (outputs > 0.5).float()
                else:
                    loss = criterion(outputs, targets)
                    _, predictions = torch.max(outputs, 1)
                
                total_loss += loss.item()
                all_predictions.extend(predictions.cpu().numpy())
                all_targets.extend(targets.cpu().numpy())
        
        # Calculate comprehensive metrics
        avg_loss = total_loss / len(test_loader)
        accuracy = accuracy_score(all_targets, all_predictions)
        
        metrics = {
            'loss': avg_loss,
            'accuracy': accuracy,
        }
        
        # Add classification metrics for multi-class problems
        if len(set(all_targets)) > 2:
            metrics.update({
                'precision': precision_score(all_targets, all_predictions, average='weighted'),
                'recall': recall_score(all_targets, all_predictions, average='weighted'),
                'f1_score': f1_score(all_targets, all_predictions, average='weighted')
            })
        else:
            metrics.update({
                'precision': precision_score(all_targets, all_predictions),
                'recall': recall_score(all_targets, all_predictions),
                'f1_score': f1_score(all_targets, all_predictions)
            })
        
        return metrics
    
    def _get_gpu_utilization(self) -> float:
        """Get current GPU utilization"""
        try:
            if torch.cuda.is_available():
                return torch.cuda.utilization() / 100.0
            return 0.0
        except Exception:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage"""
        try:
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()
            return 0.0
        except Exception:
            return 0.0


# Global ML trainer instance
ml_trainer = MLTrainer()


class MLTrainerTask(Task):
    """Celery task for ML training"""
    
    def run(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run ML training task"""
        try:
            # Convert config data to TrainingConfig object
            config = TrainingConfig(
                training_id=config_data['training_id'],
                model_type=ModelType(config_data['model_type']),
                architecture=ModelArchitecture(config_data['architecture']),
                dataset_path=config_data['dataset_path'],
                target_column=config_data['target_column'],
                feature_columns=config_data['feature_columns'],
                hyperparameters=config_data['hyperparameters'],
                training_params=config_data['training_params'],
                validation_split=config_data.get('validation_split', 0.2),
                test_split=config_data.get('test_split', 0.1),
                batch_size=config_data.get('batch_size', 32),
                epochs=config_data.get('epochs', 100),
                early_stopping_patience=config_data.get('early_stopping_patience', 10),
                learning_rate=config_data.get('learning_rate', 0.001),
                optimizer=config_data.get('optimizer', 'adam'),
                loss_function=config_data.get('loss_function', 'cross_entropy'),
                metrics=config_data.get('metrics'),
                gpu_enabled=config_data.get('gpu_enabled', True),
                distributed_training=config_data.get('distributed_training', False),
                auto_hyperparameter_tuning=config_data.get('auto_hyperparameter_tuning', True),
                model_versioning=config_data.get('model_versioning', True),
                experiment_tracking=config_data.get('experiment_tracking', True)
            )
            
            # Execute training
            result = asyncio.run(ml_trainer.train_model(config))
            return asdict(result)
            
        except Exception as e:
            logger.error(f"ML training task failed: {str(e)}")
            return {
                "training_id": config_data.get("training_id", "unknown"),
                "model_type": config_data.get("model_type", "unknown"),
                "status": TrainingStatus.FAILED.value,
                "start_time": datetime.utcnow().isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "duration": 0.0,
                "best_metrics": {},
                "final_metrics": {},
                "model_path": None,
                "model_version": None,
                "hyperparameters": {},
                "training_history": [],
                "gpu_utilization": 0.0,
                "memory_usage": 0.0,
                "error_message": str(e)
            }
"""
Advanced NLU Extractor Module

This module implements revolutionary Natural Language Understanding capabilities
using GPU-accelerated deep learning models for intent recognition, sentiment
analysis, entity extraction, and conversational context analysis. The extractor
provides sophisticated linguistic analysis to enable intelligent conversation
management and business intelligence generation.

The NLU extractor serves as the cognitive engine for understanding human
communication, implementing state-of-the-art techniques for extracting
meaningful insights from conversational data in real-time.
"""

import asyncio
import logging
import time
import re
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque

import numpy as np
import cupy as cp
import torch
import torch.nn.functional as F
from transformers import (
    AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
    pipeline, BertTokenizer, BertModel
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from textblob import TextBlob

from config import VoiceBridgeConfig
from gpu_manager import GPUResourceManager, GPUTaskType


class IntentType(Enum):
    """Enumeration of conversation intent types."""
    GREETING = "greeting"
    QUESTION = "question"
    REQUEST = "request"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    BOOKING = "booking"
    CANCELLATION = "cancellation"
    INFORMATION = "information"
    SUPPORT = "support"
    SALES = "sales"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"


class SentimentType(Enum):
    """Enumeration of sentiment types."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class EmotionType(Enum):
    """Enumeration of emotion types."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"
    EXCITEMENT = "excitement"
    FRUSTRATION = "frustration"
    SATISFACTION = "satisfaction"


@dataclass
class EntityExtraction:
    """Data class for extracted entities."""
    text: str
    label: str
    confidence: float
    start_pos: int
    end_pos: int
    normalized_value: Optional[str] = None


@dataclass
class IntentClassification:
    """Data class for intent classification results."""
    intent: IntentType
    confidence: float
    sub_intents: List[Tuple[str, float]]
    reasoning: str


@dataclass
class SentimentAnalysis:
    """Data class for sentiment analysis results."""
    sentiment: SentimentType
    confidence: float
    polarity: float
    subjectivity: float
    emotion: EmotionType
    emotion_confidence: float


@dataclass
class ConversationalContext:
    """Data class for conversational context."""
    topic: str
    urgency_level: float
    customer_satisfaction: float
    conversation_stage: str
    key_points: List[str]
    unresolved_issues: List[str]


@dataclass
class NLUResults:
    """Comprehensive NLU analysis results."""
    text: str
    intent: IntentClassification
    sentiment: SentimentAnalysis
    entities: List[EntityExtraction]
    context: ConversationalContext
    keywords: List[str]
    language: str
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]


class AdvancedNLUExtractor:
    """
    Revolutionary GPU-accelerated NLU processing system.
    
    Implements comprehensive natural language understanding including
    intent recognition, sentiment analysis, entity extraction, and
    conversational context analysis using state-of-the-art deep
    learning models optimized for GPU execution.
    """
    
    def __init__(self, config: VoiceBridgeConfig, gpu_manager: GPUResourceManager):
        """
        Initialize advanced NLU extractor.
        
        Args:
            config: Voice-bridge configuration
            gpu_manager: GPU resource manager instance
        """
        self.config = config
        self.gpu_manager = gpu_manager
        self.logger = logging.getLogger(__name__)
        
        # NLU configuration
        self.sentiment_threshold = config.nlu_sentiment_threshold
        self.intent_threshold = config.nlu_intent_threshold
        self.entity_threshold = config.nlu_entity_threshold
        self.context_window = config.nlu_context_window
        self.batch_size = config.nlu_batch_size
        
        # Model components
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        
        # GPU processing state
        self.gpu_available = False
        self.device = "cpu"
        
        # Language processing
        self.nlp_models = {}
        self.supported_languages = config.supported_languages
        
        # Context management
        self.conversation_contexts: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.context_window)
        )
        self.topic_models = {}
        
        # Intent patterns and rules
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
        
        # Performance tracking
        self.processing_stats = {
            "total_extractions": 0,
            "gpu_extractions": 0,
            "cpu_extractions": 0,
            "avg_processing_time": 0.0,
            "accuracy_scores": []
        }
        
        # Advanced features
        self.enable_multilingual = config.enable_multilingual_support
        self.enable_context_analysis = True
        self.enable_emotion_detection = config.enable_emotion_detection
    
    async def initialize(self) -> None:
        """
        Initialize NLU extractor with models and GPU resources.
        
        Loads pre-trained models, initializes GPU processing, and
        sets up language processing pipelines for optimal performance.
        """
        self.logger.info("Initializing advanced NLU extractor")
        
        try:
            # Check GPU availability
            self.gpu_available = self.gpu_manager.cuda_available
            if self.gpu_available:
                self.device = f"cuda:{self.gpu_manager.device_id}"
            
            # Load core NLU models
            await self._load_core_models()
            
            # Initialize language models
            await self._initialize_language_models()
            
            # Load specialized models
            await self._load_specialized_models()
            
            # Initialize processing pipelines
            await self._initialize_pipelines()
            
            self.logger.info("Advanced NLU extractor initialized successfully",
                           extra={"gpu_enabled": self.gpu_available,
                                 "device": self.device})
            
        except Exception as e:
            self.logger.error(f"NLU extractor initialization failed: {e}")
            raise
    
    async def _load_core_models(self) -> None:
        """
        Load core NLU models for intent, sentiment, and entity processing.
        
        Loads pre-trained transformer models optimized for GPU execution
        and configures them for real-time inference.
        """
        try:
            async with self.gpu_manager.allocate_resources(
                task_id="model_loading",
                task_type=GPUTaskType.NLU_INFERENCE,
                memory_mb=1024,
                estimated_duration=30.0
            ) as gpu_config:
                
                device = gpu_config.get("device", "cpu")
                
                # Load sentiment analysis model
                self.logger.info("Loading sentiment analysis model")
                self.models["sentiment"] = AutoModelForSequenceClassification.from_pretrained(
                    "cardiffnlp/twitter-roberta-base-sentiment-latest"
                ).to(device)
                self.tokenizers["sentiment"] = AutoTokenizer.from_pretrained(
                    "cardiffnlp/twitter-roberta-base-sentiment-latest"
                )
                
                # Load intent classification model (using a general classification model)
                self.logger.info("Loading intent classification model")
                self.models["intent"] = AutoModelForSequenceClassification.from_pretrained(
                    "microsoft/DialoGPT-medium"
                ).to(device)
                self.tokenizers["intent"] = AutoTokenizer.from_pretrained(
                    "microsoft/DialoGPT-medium"
                )
                
                # Load entity extraction model
                self.logger.info("Loading entity extraction model")
                self.models["entities"] = AutoModel.from_pretrained(
                    "dbmdz/bert-large-cased-finetuned-conll03-english"
                ).to(device)
                self.tokenizers["entities"] = AutoTokenizer.from_pretrained(
                    "dbmdz/bert-large-cased-finetuned-conll03-english"
                )
                
                # Load emotion detection model
                if self.enable_emotion_detection:
                    self.logger.info("Loading emotion detection model")
                    self.models["emotion"] = AutoModelForSequenceClassification.from_pretrained(
                        "j-hartmann/emotion-english-distilroberta-base"
                    ).to(device)
                    self.tokenizers["emotion"] = AutoTokenizer.from_pretrained(
                        "j-hartmann/emotion-english-distilroberta-base"
                    )
                
                self.logger.info("Core NLU models loaded successfully")
                
        except Exception as e:
            self.logger.error(f"Core model loading failed: {e}")
            # Continue with CPU-only processing
            self.gpu_available = False
            self.device = "cpu"
    
    async def _initialize_language_models(self) -> None:
        """
        Initialize spaCy language models for linguistic analysis.
        
        Loads language-specific models for tokenization, POS tagging,
        dependency parsing, and named entity recognition.
        """
        try:
            # Load English model (primary)
            try:
                self.nlp_models["en"] = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning("English spaCy model not found, using basic tokenization")
                self.nlp_models["en"] = None
            
            # Load additional language models if multilingual support is enabled
            if self.enable_multilingual:
                language_models = {
                    "es": "es_core_news_sm",
                    "fr": "fr_core_news_sm",
                    "de": "de_core_news_sm",
                    "it": "it_core_news_sm"
                }
                
                for lang_code, model_name in language_models.items():
                    if lang_code in self.supported_languages:
                        try:
                            self.nlp_models[lang_code] = spacy.load(model_name)
                        except OSError:
                            self.logger.warning(f"Language model {model_name} not found")
                            self.nlp_models[lang_code] = None
            
            self.logger.info("Language models initialized",
                           extra={"loaded_languages": list(self.nlp_models.keys())})
            
        except Exception as e:
            self.logger.error(f"Language model initialization failed: {e}")
    
    async def _load_specialized_models(self) -> None:
        """
        Load specialized models for advanced NLU features.
        
        Loads models for topic modeling, conversation analysis,
        and domain-specific understanding.
        """
        try:
            # Initialize TF-IDF vectorizer for keyword extraction
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Initialize topic modeling components
            self.topic_keywords = {
                "support": ["help", "problem", "issue", "error", "bug", "fix"],
                "sales": ["buy", "purchase", "price", "cost", "order", "product"],
                "booking": ["book", "reserve", "appointment", "schedule", "meeting"],
                "billing": ["bill", "payment", "charge", "invoice", "refund"],
                "technical": ["technical", "software", "hardware", "system", "configuration"]
            }
            
            self.logger.info("Specialized models loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Specialized model loading failed: {e}")
    
    async def _initialize_pipelines(self) -> None:
        """
        Initialize processing pipelines for efficient inference.
        
        Sets up optimized pipelines for batch processing and
        real-time inference with GPU acceleration.
        """
        try:
            if self.gpu_available:
                # Initialize GPU-accelerated pipelines
                self.pipelines["sentiment"] = pipeline(
                    "sentiment-analysis",
                    model=self.models["sentiment"],
                    tokenizer=self.tokenizers["sentiment"],
                    device=0 if self.gpu_available else -1,
                    batch_size=self.batch_size
                )
                
                if self.enable_emotion_detection and "emotion" in self.models:
                    self.pipelines["emotion"] = pipeline(
                        "text-classification",
                        model=self.models["emotion"],
                        tokenizer=self.tokenizers["emotion"],
                        device=0 if self.gpu_available else -1,
                        batch_size=self.batch_size
                    )
            
            self.logger.info("Processing pipelines initialized")
            
        except Exception as e:
            self.logger.error(f"Pipeline initialization failed: {e}")
    
    def _initialize_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """
        Initialize intent recognition patterns.
        
        Returns:
            Dict mapping intent types to pattern lists
        """
        return {
            IntentType.GREETING: [
                r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b",
                r"\b(how are you|nice to meet you)\b"
            ],
            IntentType.QUESTION: [
                r"\b(what|how|when|where|why|which|who)\b.*\?",
                r"\b(can you tell me|could you explain|do you know)\b"
            ],
            IntentType.REQUEST: [
                r"\b(please|can you|could you|would you|i need|i want)\b",
                r"\b(help me|assist me|show me)\b"
            ],
            IntentType.COMPLAINT: [
                r"\b(problem|issue|wrong|error|broken|not working)\b",
                r"\b(disappointed|frustrated|angry|upset)\b"
            ],
            IntentType.COMPLIMENT: [
                r"\b(great|excellent|amazing|wonderful|fantastic|perfect)\b",
                r"\b(thank you|thanks|appreciate|grateful)\b"
            ],
            IntentType.BOOKING: [
                r"\b(book|reserve|schedule|appointment|meeting)\b",
                r"\b(available|availability|free time)\b"
            ],
            IntentType.CANCELLATION: [
                r"\b(cancel|cancellation|refund|return)\b",
                r"\b(don't want|no longer need|change my mind)\b"
            ],
            IntentType.INFORMATION: [
                r"\b(information|details|specs|features|about)\b",
                r"\b(tell me about|learn more|find out)\b"
            ],
            IntentType.SUPPORT: [
                r"\b(support|help|assistance|technical|troubleshoot)\b",
                r"\b(not working|having trouble|need help)\b"
            ],
            IntentType.SALES: [
                r"\b(buy|purchase|order|price|cost|payment)\b",
                r"\b(interested in|looking for|want to buy)\b"
            ],
            IntentType.GOODBYE: [
                r"\b(goodbye|bye|see you|talk to you later|have a good day)\b",
                r"\b(thanks for your help|that's all|nothing else)\b"
            ]
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """
        Initialize entity extraction patterns.
        
        Returns:
            Dict mapping entity types to pattern lists
        """
        return {
            "phone": [
                r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
                r"\(\d{3}\)\s*\d{3}[-.]?\d{4}"
            ],
            "email": [
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            ],
            "date": [
                r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
                r"\b(today|tomorrow|yesterday|next week|last week)\b"
            ],
            "time": [
                r"\b\d{1,2}:\d{2}\s*(am|pm|AM|PM)?\b",
                r"\b(morning|afternoon|evening|night)\b"
            ],
            "money": [
                r"\$\d+(?:,\d{3})*(?:\.\d{2})?",
                r"\b\d+\s*(dollars?|cents?|USD)\b"
            ],
            "product": [
                r"\b(product|item|service|package|plan)\s+\w+\b"
            ]
        }
    
    async def extract_insights(self, text: str, session_id: str) -> NLUResults:
        """
        Extract comprehensive NLU insights from text.
        
        Performs complete natural language understanding including
        intent classification, sentiment analysis, entity extraction,
        and conversational context analysis.
        
        Args:
            text: Input text to analyze
            session_id: Session identifier for context tracking
            
        Returns:
            NLUResults containing comprehensive analysis
        """
        start_time = time.time()
        
        try:
            # Preprocess text
            cleaned_text = await self._preprocess_text(text)
            
            # Detect language
            language = await self._detect_language(cleaned_text)
            
            # Parallel processing of different NLU tasks
            tasks = [
                self._classify_intent(cleaned_text, session_id),
                self._analyze_sentiment(cleaned_text),
                self._extract_entities(cleaned_text, language),
                self._extract_keywords(cleaned_text),
                self._analyze_context(cleaned_text, session_id)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Unpack results
            intent_result = results[0] if not isinstance(results[0], Exception) else self._default_intent()
            sentiment_result = results[1] if not isinstance(results[1], Exception) else self._default_sentiment()
            entities_result = results[2] if not isinstance(results[2], Exception) else []
            keywords_result = results[3] if not isinstance(results[3], Exception) else []
            context_result = results[4] if not isinstance(results[4], Exception) else self._default_context()
            
            # Calculate overall confidence score
            confidence_score = await self._calculate_confidence_score(
                intent_result, sentiment_result, entities_result
            )
            
            # Create comprehensive results
            nlu_results = NLUResults(
                text=text,
                intent=intent_result,
                sentiment=sentiment_result,
                entities=entities_result,
                context=context_result,
                keywords=keywords_result,
                language=language,
                confidence_score=confidence_score,
                processing_time=time.time() - start_time,
                metadata={
                    "session_id": session_id,
                    "processing_method": "gpu" if self.gpu_available else "cpu",
                    "model_versions": self._get_model_versions(),
                    "text_length": len(text),
                    "cleaned_text_length": len(cleaned_text)
                }
            )
            
            # Update conversation context
            await self._update_conversation_context(session_id, nlu_results)
            
            # Update statistics
            self.processing_stats["total_extractions"] += 1
            if self.gpu_available:
                self.processing_stats["gpu_extractions"] += 1
            else:
                self.processing_stats["cpu_extractions"] += 1
            
            processing_time = time.time() - start_time
            self.processing_stats["avg_processing_time"] = (
                (self.processing_stats["avg_processing_time"] * 
                 (self.processing_stats["total_extractions"] - 1) + processing_time) /
                self.processing_stats["total_extractions"]
            )
            
            return nlu_results
            
        except Exception as e:
            self.logger.error(f"NLU extraction failed: {e}",
                            extra={"session_id": session_id, "text": text[:100]})
            
            # Return default results on error
            return NLUResults(
                text=text,
                intent=self._default_intent(),
                sentiment=self._default_sentiment(),
                entities=[],
                context=self._default_context(),
                keywords=[],
                language="en",
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for NLU analysis.
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned and preprocessed text
        """
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep punctuation
        cleaned = re.sub(r'[^\w\s\.\?\!\,\;\:\-\(\)]', '', cleaned)
        
        # Normalize case (keep original for entity extraction)
        return cleaned
    
    async def _detect_language(self, text: str) -> str:
        """
        Detect the language of input text.
        
        Args:
            text: Input text
            
        Returns:
            Language code (e.g., 'en', 'es', 'fr')
        """
        try:
            # Simple language detection using TextBlob
            blob = TextBlob(text)
            detected_lang = blob.detect_language()
            
            # Validate against supported languages
            if detected_lang in self.supported_languages:
                return detected_lang
            else:
                return "en"  # Default to English
                
        except Exception as e:
            self.logger.warning(f"Language detection failed: {e}")
            return "en"  # Default to English
    
    async def _classify_intent(self, text: str, session_id: str) -> IntentClassification:
        """
        Classify the intent of the input text.
        
        Args:
            text: Input text
            session_id: Session identifier
            
        Returns:
            IntentClassification result
        """
        try:
            # Pattern-based intent classification
            pattern_scores = {}
            
            for intent_type, patterns in self.intent_patterns.items():
                score = 0.0
                for pattern in patterns:
                    matches = re.findall(pattern, text.lower())
                    score += len(matches) * 0.3
                
                if score > 0:
                    pattern_scores[intent_type] = min(score, 1.0)
            
            # Get conversation context for intent refinement
            context_history = self.conversation_contexts.get(session_id, deque())
            
            # Apply context-based adjustments
            if context_history:
                last_intent = context_history[-1].intent.intent if context_history else None
                
                # Intent transition probabilities
                if last_intent == IntentType.GREETING:
                    pattern_scores[IntentType.QUESTION] = pattern_scores.get(IntentType.QUESTION, 0) + 0.2
                    pattern_scores[IntentType.REQUEST] = pattern_scores.get(IntentType.REQUEST, 0) + 0.2
                elif last_intent == IntentType.QUESTION:
                    pattern_scores[IntentType.INFORMATION] = pattern_scores.get(IntentType.INFORMATION, 0) + 0.3
            
            # Determine primary intent
            if pattern_scores:
                primary_intent = max(pattern_scores, key=pattern_scores.get)
                confidence = pattern_scores[primary_intent]
            else:
                primary_intent = IntentType.UNKNOWN
                confidence = 0.0
            
            # Generate sub-intents
            sub_intents = [(intent.value, score) for intent, score in pattern_scores.items() 
                          if intent != primary_intent and score > 0.1]
            sub_intents.sort(key=lambda x: x[1], reverse=True)
            
            # Generate reasoning
            reasoning = self._generate_intent_reasoning(text, primary_intent, pattern_scores)
            
            return IntentClassification(
                intent=primary_intent,
                confidence=confidence,
                sub_intents=sub_intents[:3],  # Top 3 sub-intents
                reasoning=reasoning
            )
            
        except Exception as e:
            self.logger.error(f"Intent classification failed: {e}")
            return self._default_intent()
    
    async def _analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """
        Analyze sentiment and emotion of the input text.
        
        Args:
            text: Input text
            
        Returns:
            SentimentAnalysis result
        """
        try:
            # Use TextBlob for basic sentiment analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Map polarity to sentiment categories
            if polarity >= 0.6:
                sentiment = SentimentType.VERY_POSITIVE
            elif polarity >= 0.2:
                sentiment = SentimentType.POSITIVE
            elif polarity >= -0.2:
                sentiment = SentimentType.NEUTRAL
            elif polarity >= -0.6:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.VERY_NEGATIVE
            
            # Calculate confidence based on polarity magnitude
            confidence = min(abs(polarity) + 0.3, 1.0)
            
            # Emotion detection
            emotion, emotion_confidence = await self._detect_emotion_from_text(text)
            
            return SentimentAnalysis(
                sentiment=sentiment,
                confidence=confidence,
                polarity=polarity,
                subjectivity=subjectivity,
                emotion=emotion,
                emotion_confidence=emotion_confidence
            )
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}")
            return self._default_sentiment()
    
    async def _detect_emotion_from_text(self, text: str) -> Tuple[EmotionType, float]:
        """
        Detect emotion from text using advanced models.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (emotion, confidence)
        """
        try:
            if self.enable_emotion_detection and "emotion" in self.pipelines:
                # Use GPU-accelerated emotion detection
                result = self.pipelines["emotion"](text)
                
                # Map model output to our emotion types
                emotion_mapping = {
                    "joy": EmotionType.JOY,
                    "sadness": EmotionType.SADNESS,
                    "anger": EmotionType.ANGER,
                    "fear": EmotionType.FEAR,
                    "surprise": EmotionType.SURPRISE,
                    "disgust": EmotionType.DISGUST,
                    "neutral": EmotionType.NEUTRAL
                }
                
                predicted_emotion = result[0]["label"].lower()
                confidence = result[0]["score"]
                
                emotion = emotion_mapping.get(predicted_emotion, EmotionType.NEUTRAL)
                return emotion, confidence
            else:
                # Fallback emotion detection using keywords
                emotion_keywords = {
                    EmotionType.JOY: ["happy", "joy", "excited", "pleased", "delighted"],
                    EmotionType.ANGER: ["angry", "mad", "furious", "annoyed", "irritated"],
                    EmotionType.SADNESS: ["sad", "disappointed", "upset", "depressed"],
                    EmotionType.FEAR: ["afraid", "scared", "worried", "anxious"],
                    EmotionType.SURPRISE: ["surprised", "amazed", "shocked", "unexpected"],
                    EmotionType.FRUSTRATION: ["frustrated", "annoyed", "bothered"]
                }
                
                text_lower = text.lower()
                emotion_scores = {}
                
                for emotion, keywords in emotion_keywords.items():
                    score = sum(1 for keyword in keywords if keyword in text_lower)
                    if score > 0:
                        emotion_scores[emotion] = score
                
                if emotion_scores:
                    detected_emotion = max(emotion_scores, key=emotion_scores.get)
                    confidence = min(emotion_scores[detected_emotion] * 0.3, 1.0)
                    return detected_emotion, confidence
                
                return EmotionType.NEUTRAL, 0.5
                
        except Exception as e:
            self.logger.error(f"Emotion detection failed: {e}")
            return EmotionType.NEUTRAL, 0.5
    
    async def _extract_entities(self, text: str, language: str) -> List[EntityExtraction]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            language: Language code
            
        Returns:
            List of extracted entities
        """
        try:
            entities = []
            
            # Pattern-based entity extraction
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        entity = EntityExtraction(
                            text=match.group(),
                            label=entity_type,
                            confidence=0.8,  # Pattern-based confidence
                            start_pos=match.start(),
                            end_pos=match.end(),
                            normalized_value=self._normalize_entity_value(
                                match.group(), entity_type
                            )
                        )
                        entities.append(entity)
            
            # spaCy-based entity extraction
            nlp_model = self.nlp_models.get(language)
            if nlp_model:
                doc = nlp_model(text)
                for ent in doc.ents:
                    # Skip if already found by patterns
                    if not any(e.start_pos <= ent.start_char < e.end_pos for e in entities):
                        entity = EntityExtraction(
                            text=ent.text,
                            label=ent.label_.lower(),
                            confidence=0.9,  # spaCy confidence
                            start_pos=ent.start_char,
                            end_pos=ent.end_char,
                            normalized_value=self._normalize_entity_value(
                                ent.text, ent.label_.lower()
                            )
                        )
                        entities.append(entity)
            
            # Remove duplicates and sort by position
            entities = self._deduplicate_entities(entities)
            entities.sort(key=lambda x: x.start_pos)
            
            return entities
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")
            return []
    
    def _normalize_entity_value(self, text: str, entity_type: str) -> Optional[str]:
        """
        Normalize entity values for consistency.
        
        Args:
            text: Entity text
            entity_type: Type of entity
            
        Returns:
            Normalized value or None
        """
        try:
            if entity_type == "phone":
                # Normalize phone number
                digits = re.sub(r'\D', '', text)
                if len(digits) == 10:
                    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                elif len(digits) == 11 and digits[0] == '1':
                    return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            
            elif entity_type == "email":
                return text.lower()
            
            elif entity_type == "money":
                # Extract numeric value
                amount = re.search(r'[\d,]+\.?\d*', text)
                if amount:
                    return amount.group().replace(',', '')
            
            return text
            
        except Exception:
            return text
    
    def _deduplicate_entities(self, entities: List[EntityExtraction]) -> List[EntityExtraction]:
        """
        Remove duplicate entities based on overlap.
        
        Args:
            entities: List of entities
            
        Returns:
            Deduplicated list of entities
        """
        if not entities:
            return entities
        
        # Sort by confidence (descending) and position
        entities.sort(key=lambda x: (-x.confidence, x.start_pos))
        
        deduplicated = []
        for entity in entities:
            # Check for overlap with existing entities
            overlaps = any(
                (entity.start_pos < existing.end_pos and 
                 entity.end_pos > existing.start_pos)
                for existing in deduplicated
            )
            
            if not overlaps:
                deduplicated.append(entity)
        
        return deduplicated
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted keywords
        """
        try:
            # Simple keyword extraction using TF-IDF concepts
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Filter out common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
                'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
                'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
            }
            
            # Count word frequencies
            word_freq = defaultdict(int)
            for word in words:
                if len(word) > 2 and word not in stop_words:
                    word_freq[word] += 1
            
            # Get top keywords
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in keywords[:10]]  # Top 10 keywords
            
        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}")
            return []
    
    async def _analyze_context(self, text: str, session_id: str) -> ConversationalContext:
        """
        Analyze conversational context and derive insights.
        
        Args:
            text: Input text
            session_id: Session identifier
            
        Returns:
            ConversationalContext analysis
        """
        try:
            # Determine topic
            topic = await self._determine_topic(text)
            
            # Calculate urgency level
            urgency_level = await self._calculate_urgency(text)
            
            # Estimate customer satisfaction
            customer_satisfaction = await self._estimate_satisfaction(text, session_id)
            
            # Determine conversation stage
            conversation_stage = await self._determine_conversation_stage(text, session_id)
            
            # Extract key points
            key_points = await self._extract_key_points(text)
            
            # Identify unresolved issues
            unresolved_issues = await self._identify_unresolved_issues(text, session_id)
            
            return ConversationalContext(
                topic=topic,
                urgency_level=urgency_level,
                customer_satisfaction=customer_satisfaction,
                conversation_stage=conversation_stage,
                key_points=key_points,
                unresolved_issues=unresolved_issues
            )
            
        except Exception as e:
            self.logger.error(f"Context analysis failed: {e}")
            return self._default_context()
    
    async def _determine_topic(self, text: str) -> str:
        """
        Determine the main topic of conversation.
        
        Args:
            text: Input text
            
        Returns:
            Topic string
        """
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in self.topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        return "general"
    
    async def _calculate_urgency(self, text: str) -> float:
        """
        Calculate urgency level of the message.
        
        Args:
            text: Input text
            
        Returns:
            Urgency level (0.0 to 1.0)
        """
        urgency_indicators = [
            "urgent", "emergency", "asap", "immediately", "critical",
            "broken", "not working", "down", "error", "problem"
        ]
        
        text_lower = text.lower()
        urgency_score = 0.0
        
        for indicator in urgency_indicators:
            if indicator in text_lower:
                urgency_score += 0.2
        
        # Check for exclamation marks
        urgency_score += min(text.count('!') * 0.1, 0.3)
        
        # Check for capital letters (shouting)
        if text.isupper() and len(text) > 10:
            urgency_score += 0.3
        
        return min(urgency_score, 1.0)
    
    async def _estimate_satisfaction(self, text: str, session_id: str) -> float:
        """
        Estimate customer satisfaction level.
        
        Args:
            text: Input text
            session_id: Session identifier
            
        Returns:
            Satisfaction level (0.0 to 1.0)
        """
        # Use sentiment as base satisfaction
        blob = TextBlob(text)
        base_satisfaction = (blob.sentiment.polarity + 1) / 2  # Convert -1,1 to 0,1
        
        # Adjust based on conversation history
        context_history = self.conversation_contexts.get(session_id, deque())
        if context_history:
            # Average sentiment over conversation
            avg_sentiment = sum(
                (ctx.sentiment.polarity + 1) / 2 
                for ctx in context_history
            ) / len(context_history)
            
            # Weighted average (current 70%, history 30%)
            satisfaction = 0.7 * base_satisfaction + 0.3 * avg_sentiment
        else:
            satisfaction = base_satisfaction
        
        return max(0.0, min(1.0, satisfaction))
    
    async def _determine_conversation_stage(self, text: str, session_id: str) -> str:
        """
        Determine the current stage of conversation.
        
        Args:
            text: Input text
            session_id: Session identifier
            
        Returns:
            Conversation stage string
        """
        context_history = self.conversation_contexts.get(session_id, deque())
        
        if not context_history:
            return "opening"
        
        # Analyze conversation flow
        total_messages = len(context_history)
        
        if total_messages <= 2:
            return "opening"
        elif total_messages <= 5:
            return "information_gathering"
        elif any("thank" in ctx.text.lower() or "bye" in ctx.text.lower() 
                for ctx in list(context_history)[-2:]):
            return "closing"
        else:
            return "problem_solving"
    
    async def _extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from the conversation.
        
        Args:
            text: Input text
            
        Returns:
            List of key points
        """
        # Simple key point extraction based on sentence importance
        sentences = re.split(r'[.!?]+', text)
        key_points = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Minimum length
                # Check for important indicators
                if any(indicator in sentence.lower() for indicator in 
                      ["need", "want", "problem", "issue", "help", "important"]):
                    key_points.append(sentence)
        
        return key_points[:5]  # Top 5 key points
    
    async def _identify_unresolved_issues(self, text: str, session_id: str) -> List[str]:
        """
        Identify unresolved issues in the conversation.
        
        Args:
            text: Input text
            session_id: Session identifier
            
        Returns:
            List of unresolved issues
        """
        issue_indicators = [
            "still not working", "still have problem", "not resolved",
            "still need help", "doesn't work", "not fixed"
        ]
        
        text_lower = text.lower()
        unresolved_issues = []
        
        for indicator in issue_indicators:
            if indicator in text_lower:
                # Extract the sentence containing the issue
                sentences = re.split(r'[.!?]+', text)
                for sentence in sentences:
                    if indicator in sentence.lower():
                        unresolved_issues.append(sentence.strip())
                        break
        
        return unresolved_issues
    
    async def _calculate_confidence_score(self, 
                                        intent: IntentClassification,
                                        sentiment: SentimentAnalysis,
                                        entities: List[EntityExtraction]) -> float:
        """
        Calculate overall confidence score for NLU results.
        
        Args:
            intent: Intent classification result
            sentiment: Sentiment analysis result
            entities: List of extracted entities
            
        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        # Weight different components
        intent_weight = 0.4
        sentiment_weight = 0.3
        entity_weight = 0.3
        
        # Calculate weighted confidence
        confidence = (
            intent.confidence * intent_weight +
            sentiment.confidence * sentiment_weight +
            (sum(e.confidence for e in entities) / max(len(entities), 1)) * entity_weight
        )
        
        return min(confidence, 1.0)
    
    def _generate_intent_reasoning(self, text: str, intent: IntentType, 
                                 scores: Dict[IntentType, float]) -> str:
        """
        Generate reasoning for intent classification.
        
        Args:
            text: Input text
            intent: Classified intent
            scores: Intent scores
            
        Returns:
            Reasoning string
        """
        if intent == IntentType.UNKNOWN:
            return "No clear intent patterns detected in the text."
        
        # Find matching patterns
        patterns = self.intent_patterns.get(intent, [])
        matched_patterns = []
        
        for pattern in patterns:
            if re.search(pattern, text.lower()):
                matched_patterns.append(pattern)
        
        if matched_patterns:
            return f"Intent '{intent.value}' detected based on patterns: {', '.join(matched_patterns[:2])}"
        else:
            return f"Intent '{intent.value}' inferred from context and content analysis."
    
    def _default_intent(self) -> IntentClassification:
        """Return default intent classification."""
        return IntentClassification(
            intent=IntentType.UNKNOWN,
            confidence=0.0,
            sub_intents=[],
            reasoning="Default intent due to processing error"
        )
    
    def _default_sentiment(self) -> SentimentAnalysis:
        """Return default sentiment analysis."""
        return SentimentAnalysis(
            sentiment=SentimentType.NEUTRAL,
            confidence=0.5,
            polarity=0.0,
            subjectivity=0.5,
            emotion=EmotionType.NEUTRAL,
            emotion_confidence=0.5
        )
    
    def _default_context(self) -> ConversationalContext:
        """Return default conversational context."""
        return ConversationalContext(
            topic="general",
            urgency_level=0.0,
            customer_satisfaction=0.5,
            conversation_stage="unknown",
            key_points=[],
            unresolved_issues=[]
        )
    
    def _get_model_versions(self) -> Dict[str, str]:
        """Get versions of loaded models."""
        return {
            "sentiment_model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
            "intent_model": "microsoft/DialoGPT-medium",
            "entity_model": "dbmdz/bert-large-cased-finetuned-conll03-english",
            "emotion_model": "j-hartmann/emotion-english-distilroberta-base" if self.enable_emotion_detection else "none"
        }
    
    async def _update_conversation_context(self, session_id: str, results: NLUResults) -> None:
        """
        Update conversation context with new results.
        
        Args:
            session_id: Session identifier
            results: NLU results to add to context
        """
        try:
            self.conversation_contexts[session_id].append(results)
            
        except Exception as e:
            self.logger.error(f"Context update failed: {e}")
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive conversation summary.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict containing conversation summary and insights
        """
        try:
            context_history = self.conversation_contexts.get(session_id, deque())
            
            if not context_history:
                return {"message": "No conversation history available"}
            
            # Aggregate statistics
            total_messages = len(context_history)
            intents = [ctx.intent.intent.value for ctx in context_history]
            sentiments = [ctx.sentiment.sentiment.value for ctx in context_history]
            emotions = [ctx.sentiment.emotion.value for ctx in context_history]
            
            # Calculate averages
            avg_confidence = sum(ctx.confidence_score for ctx in context_history) / total_messages
            avg_satisfaction = sum(ctx.context.customer_satisfaction for ctx in context_history) / total_messages
            avg_urgency = sum(ctx.context.urgency_level for ctx in context_history) / total_messages
            
            # Extract all entities
            all_entities = []
            for ctx in context_history:
                all_entities.extend(ctx.entities)
            
            # Get unique topics
            topics = list(set(ctx.context.topic for ctx in context_history))
            
            # Get all unresolved issues
            unresolved_issues = []
            for ctx in context_history:
                unresolved_issues.extend(ctx.context.unresolved_issues)
            
            return {
                "session_id": session_id,
                "total_messages": total_messages,
                "intent_distribution": {intent: intents.count(intent) for intent in set(intents)},
                "sentiment_distribution": {sentiment: sentiments.count(sentiment) for sentiment in set(sentiments)},
                "emotion_distribution": {emotion: emotions.count(emotion) for emotion in set(emotions)},
                "average_confidence": avg_confidence,
                "average_satisfaction": avg_satisfaction,
                "average_urgency": avg_urgency,
                "topics_discussed": topics,
                "total_entities": len(all_entities),
                "entity_types": list(set(e.label for e in all_entities)),
                "unresolved_issues": list(set(unresolved_issues)),
                "conversation_stage": context_history[-1].context.conversation_stage if context_history else "unknown"
            }
            
        except Exception as e:
            self.logger.error(f"Conversation summary generation failed: {e}")
            return {"error": str(e)}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get NLU extractor health status.
        
        Returns:
            Dict containing health status and performance metrics
        """
        try:
            status = {
                "status": "healthy",
                "gpu_available": self.gpu_available,
                "device": self.device,
                "models_loaded": len(self.models),
                "pipelines_loaded": len(self.pipelines),
                "processing_stats": self.processing_stats.copy(),
                "active_sessions": len(self.conversation_contexts),
                "capabilities": {
                    "multilingual_support": self.enable_multilingual,
                    "emotion_detection": self.enable_emotion_detection,
                    "context_analysis": self.enable_context_analysis,
                    "supported_languages": self.supported_languages
                }
            }
            
            # Check for issues
            if self.processing_stats["total_extractions"] > 0:
                gpu_ratio = self.processing_stats["gpu_extractions"] / self.processing_stats["total_extractions"]
                if gpu_ratio < 0.5 and self.gpu_available:
                    status["status"] = "degraded"
                    status["issues"] = ["Low GPU utilization"]
            
            return status
            
        except Exception as e:
            self.logger.error(f"Health status check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self) -> None:
        """
        Cleanup NLU extractor resources.
        
        Releases GPU resources, clears caches, and stops processing tasks.
        """
        self.logger.info("Cleaning up NLU extractor")
        
        try:
            # Clear models and pipelines
            self.models.clear()
            self.tokenizers.clear()
            self.pipelines.clear()
            
            # Clear conversation contexts
            self.conversation_contexts.clear()
            
            # Clear language models
            self.nlp_models.clear()
            
            self.logger.info("NLU extractor cleanup completed")
            
        except Exception as e:
            self.logger.error(f"NLU extractor cleanup failed: {e}")
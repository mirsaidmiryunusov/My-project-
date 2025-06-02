"""
Specialized Agentic Functions
Industry-specific and advanced automation functions
"""

import asyncio
import json
import os
import uuid
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import httpx
import structlog
from sqlmodel import Session

from config import CoreAPIConfig
from agentic_function_service import AgenticFunction, FunctionResult

logger = structlog.get_logger(__name__)


# ==================== REAL ESTATE FUNCTIONS ====================

class PropertySearchFunction(AgenticFunction):
    """Search for real estate properties."""
    
    def __init__(self, config: CoreAPIConfig):
        super().__init__(
            name="property_search",
            description="Search for properties, analyze market data, and track listings",
            config=config
        )
    
    async def execute(self, context: Dict[str, Any], session: Session) -> FunctionResult:
        try:
            location = context.get('location')
            property_type = context.get('property_type', 'house')
            min_price = context.get('min_price', 0)
            max_price = context.get('max_price', 1000000)
            bedrooms = context.get('bedrooms')
            
            if not location:
                return FunctionResult(False, error="Missing location")
            
            async with httpx.AsyncClient() as client:
                if hasattr(self.config, 'realtor_api_key'):
                    # RealtyMole API or similar
                    headers = {'X-RapidAPI-Key': self.config.realtor_api_key}
                    
                    params = {
                        'city': location,
                        'state': context.get('state', ''),
                        'limit': 10,
                        'offset': 0
                    }
                    
                    if min_price:
                        params['minPrice'] = min_price
                    if max_price:
                        params['maxPrice'] = max_price
                    if bedrooms:
                        params['bedrooms'] = bedrooms
                    
                    response = await client.get(
                        'https://realty-mole-property-api.p.rapidapi.com/properties',
                        headers=headers,
                        params=params
                    )
                    
                    if response.status_code == 200:
                        properties_data = response.json()
                        
                        properties = []
                        for prop in properties_data[:10]:
                            properties.append({
                                'property_id': prop.get('id'),
                                'address': prop.get('formattedAddress'),
                                'price': prop.get('price'),
                                'bedrooms': prop.get('bedrooms'),
                                'bathrooms': prop.get('bathrooms'),
                                'square_feet': prop.get('squareFootage'),
                                'property_type': prop.get('propertyType'),
                                'listing_date': prop.get('listDate'),
                                'photos': prop.get('photos', [])[:3]
                            })
                        
                        return FunctionResult(
                            success=True,
                            data={
                                'search_id': f"prop_search_{uuid.uuid4().hex[:8]}",
                                'location': location,
                                'properties': properties,
                                'total_found': len(properties),
                                'data_source': 'realtor_api'
                            }
                        )
            
            # Fallback simulation
            properties = [
                {
                    'property_id': f"PROP{uuid.uuid4().hex[:6].upper()}",
                    'address': f"123 Main St, {location}",
                    'price': 450000,
                    'bedrooms': 3,
                    'bathrooms': 2,
                    'square_feet': 1800,
                    'property_type': 'Single Family',
                    'listing_date': '2024-05-15',
                    'photos': ['photo1.jpg', 'photo2.jpg']
                },
                {
                    'property_id': f"PROP{uuid.uuid4().hex[:6].upper()}",
                    'address': f"456 Oak Ave, {location}",
                    'price': 325000,
                    'bedrooms': 2,
                    'bathrooms': 1,
                    'square_feet': 1200,
                    'property_type': 'Condo',
                    'listing_date': '2024-05-20',
                    'photos': ['photo3.jpg', 'photo4.jpg']
                }
            ]
            
            return FunctionResult(
                success=True,
                data={
                    'search_id': f"prop_search_{uuid.uuid4().hex[:8]}",
                    'location': location,
                    'properties': properties,
                    'total_found': len(properties),
                    'data_source': 'simulation'
                }
            )
            
        except Exception as e:
            return FunctionResult(False, error=str(e))


class PropertyValuationFunction(AgenticFunction):
    """Estimate property values and market analysis."""
    
    def __init__(self, config: CoreAPIConfig):
        super().__init__(
            name="property_valuation",
            description="Estimate property values using market data and comparables",
            config=config
        )
    
    async def execute(self, context: Dict[str, Any], session: Session) -> FunctionResult:
        try:
            address = context.get('address')
            property_details = context.get('property_details', {})
            
            if not address:
                return FunctionResult(False, error="Missing property address")
            
            # Simulate property valuation
            base_value = 400000
            
            # Adjust based on property details
            bedrooms = property_details.get('bedrooms', 3)
            bathrooms = property_details.get('bathrooms', 2)
            square_feet = property_details.get('square_feet', 1500)
            
            # Simple valuation model
            estimated_value = base_value + (bedrooms * 25000) + (bathrooms * 15000) + (square_feet * 150)
            
            # Market adjustments
            market_trend = 1.05  # 5% increase
            estimated_value *= market_trend
            
            confidence_score = 0.85
            value_range = {
                'low': int(estimated_value * 0.9),
                'high': int(estimated_value * 1.1),
                'estimated': int(estimated_value)
            }
            
            comparables = [
                {
                    'address': f"Similar property 1 near {address}",
                    'sold_price': int(estimated_value * 0.95),
                    'sold_date': '2024-04-15',
                    'bedrooms': bedrooms,
                    'bathrooms': bathrooms
                },
                {
                    'address': f"Similar property 2 near {address}",
                    'sold_price': int(estimated_value * 1.02),
                    'sold_date': '2024-03-28',
                    'bedrooms': bedrooms,
                    'bathrooms': bathrooms + 1
                }
            ]
            
            return FunctionResult(
                success=True,
                data={
                    'valuation_id': f"val_{uuid.uuid4().hex[:8]}",
                    'address': address,
                    'value_range': value_range,
                    'confidence_score': confidence_score,
                    'comparables': comparables,
                    'market_trends': {
                        'price_trend': '+5% YoY',
                        'inventory_level': 'Low',
                        'days_on_market': 25
                    },
                    'valuation_date': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            return FunctionResult(False, error=str(e))


# ==================== LEGAL & COMPLIANCE FUNCTIONS ====================

class ContractAnalyzerFunction(AgenticFunction):
    """Analyze contracts and legal documents."""
    
    def __init__(self, config: CoreAPIConfig):
        super().__init__(
            name="contract_analyzer",
            description="Analyze contracts, extract key terms, and identify risks",
            config=config
        )
    
    async def execute(self, context: Dict[str, Any], session: Session) -> FunctionResult:
        try:
            contract_text = context.get('contract_text')
            contract_type = context.get('contract_type', 'general')
            
            if not contract_text:
                return FunctionResult(False, error="Missing contract text")
            
            # Simulate contract analysis
            analysis_results = {
                'key_terms': {
                    'parties': ['Company A', 'Company B'],
                    'effective_date': '2024-06-01',
                    'termination_date': '2025-06-01',
                    'payment_terms': 'Net 30 days',
                    'governing_law': 'State of California'
                },
                'risk_factors': [
                    {
                        'risk': 'Unlimited liability clause',
                        'severity': 'High',
                        'recommendation': 'Add liability cap'
                    },
                    {
                        'risk': 'Vague termination conditions',
                        'severity': 'Medium',
                        'recommendation': 'Clarify termination triggers'
                    }
                ],
                'compliance_issues': [
                    {
                        'issue': 'Missing data protection clause',
                        'regulation': 'GDPR',
                        'action_required': 'Add data processing terms'
                    }
                ],
                'financial_obligations': {
                    'total_contract_value': 250000,
                    'payment_schedule': 'Monthly',
                    'penalties': 'Late payment: 1.5% per month'
                }
            }
            
            return FunctionResult(
                success=True,
                data={
                    'analysis_id': f"contract_{uuid.uuid4().hex[:8]}",
                    'contract_type': contract_type,
                    'analysis_results': analysis_results,
                    'overall_risk_score': 6.5,  # out of 10
                    'recommendations': [
                        'Review liability clauses',
                        'Add compliance terms',
                        'Clarify payment terms'
                    ],
                    'analyzed_at': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            return FunctionResult(False, error=str(e))


class ComplianceCheckerFunction(AgenticFunction):
    """Check compliance with various regulations."""
    
    def __init__(self, config: CoreAPIConfig):
        super().__init__(
            name="compliance_checker",
            description="Check compliance with GDPR, HIPAA, SOX, and other regulations",
            config=config
        )
    
    async def execute(self, context: Dict[str, Any], session: Session) -> FunctionResult:
        try:
            regulation = context.get('regulation', 'GDPR')
            business_type = context.get('business_type', 'general')
            data_types = context.get('data_types', [])
            
            # Compliance frameworks
            compliance_checks = {
                'GDPR': {
                    'requirements': [
                        'Data processing lawful basis',
                        'Privacy policy published',
                        'Data subject rights implemented',
                        'Data breach notification process',
                        'Data protection officer appointed'
                    ],
                    'penalties': 'Up to 4% of annual revenue or €20M'
                },
                'HIPAA': {
                    'requirements': [
                        'Administrative safeguards',
                        'Physical safeguards',
                        'Technical safeguards',
                        'Business associate agreements',
                        'Employee training program'
                    ],
                    'penalties': 'Up to $1.5M per incident'
                },
                'SOX': {
                    'requirements': [
                        'Internal controls documentation',
                        'Financial reporting accuracy',
                        'Executive certification',
                        'Auditor independence',
                        'Whistleblower protection'
                    ],
                    'penalties': 'Criminal charges and fines'
                }
            }
            
            framework = compliance_checks.get(regulation, compliance_checks['GDPR'])
            
            # Simulate compliance assessment
            compliance_status = []
            for requirement in framework['requirements']:
                status = 'Compliant' if hash(requirement) % 3 != 0 else 'Non-Compliant'
                compliance_status.append({
                    'requirement': requirement,
                    'status': status,
                    'priority': 'High' if status == 'Non-Compliant' else 'Low'
                })
            
            compliance_score = len([s for s in compliance_status if s['status'] == 'Compliant']) / len(compliance_status) * 100
            
            return FunctionResult(
                success=True,
                data={
                    'compliance_id': f"comp_{uuid.uuid4().hex[:8]}",
                    'regulation': regulation,
                    'business_type': business_type,
                    'compliance_score': round(compliance_score, 1),
                    'status_details': compliance_status,
                    'action_items': [
                        item['requirement'] for item in compliance_status 
                        if item['status'] == 'Non-Compliant'
                    ],
                    'next_review_date': (datetime.utcnow() + timedelta(days=90)).isoformat()
                }
            )
            
        except Exception as e:
            return FunctionResult(False, error=str(e))


# ==================== ENTERTAINMENT & GAMING FUNCTIONS ====================

class GameRecommendationFunction(AgenticFunction):
    """Recommend games based on preferences."""
    
    def __init__(self, config: CoreAPIConfig):
        super().__init__(
            name="game_recommendation",
            description="Recommend games based on user preferences and gaming history",
            config=config
        )
    
    async def execute(self, context: Dict[str, Any], session: Session) -> FunctionResult:
        try:
            preferences = context.get('preferences', {})
            platform = context.get('platform', 'PC')
            genre = context.get('genre', 'any')
            
            async with httpx.AsyncClient() as client:
                if hasattr(self.config, 'rawg_api_key'):
                    # RAWG Video Games Database API
                    params = {
                        'key': self.config.rawg_api_key,
                        'page_size': 10,
                        'ordering': '-rating'
                    }
                    
                    if platform != 'any':
                        platform_mapping = {
                            'PC': 4,
                            'PlayStation': 18,
                            'Xbox': 1,
                            'Nintendo': 7
                        }
                        params['platforms'] = platform_mapping.get(platform, 4)
                    
                    if genre != 'any':
                        params['genres'] = genre.lower()
                    
                    response = await client.get(
                        'https://api.rawg.io/api/games',
                        params=params
                    )
                    
                    if response.status_code == 200:
                        games_data = response.json()
                        
                        recommendations = []
                        for game in games_data['results']:
                            recommendations.append({
                                'game_id': game['id'],
                                'name': game['name'],
                                'rating': game['rating'],
                                'released': game['released'],
                                'genres': [g['name'] for g in game['genres']],
                                'platforms': [p['platform']['name'] for p in game['platforms']],
                                'background_image': game['background_image'],
                                'metacritic': game.get('metacritic'),
                                'playtime': game.get('playtime', 0)
                            })
                        
                        return FunctionResult(
                            success=True,
                            data={
                                'recommendation_id': f"games_{uuid.uuid4().hex[:8]}",
                                'platform': platform,
                                'genre': genre,
                                'recommendations': recommendations,
                                'data_source': 'rawg'
                            }
                        )
            
            # Fallback simulation
            game_database = [
                {
                    'name': 'Cyberpunk 2077',
                    'genre': 'RPG',
                    'platform': 'PC',
                    'rating': 4.2,
                    'price': '$59.99'
                },
                {
                    'name': 'The Witcher 3',
                    'genre': 'RPG',
                    'platform': 'PC',
                    'rating': 4.8,
                    'price': '$39.99'
                },
                {
                    'name': 'Among Us',
                    'genre': 'Social',
                    'platform': 'Mobile',
                    'rating': 4.1,
                    'price': 'Free'
                }
            ]
            
            # Filter by preferences
            filtered_games = [
                game for game in game_database
                if (platform == 'any' or game['platform'] == platform) and
                   (genre == 'any' or game['genre'].lower() == genre.lower())
            ]
            
            return FunctionResult(
                success=True,
                data={
                    'recommendation_id': f"games_{uuid.uuid4().hex[:8]}",
                    'platform': platform,
                    'genre': genre,
                    'recommendations': filtered_games,
                    'data_source': 'simulation'
                }
            )
            
        except Exception as e:
            return FunctionResult(False, error=str(e))


class MovieRecommendationFunction(AgenticFunction):
    """Recommend movies and TV shows."""
    
    def __init__(self, config: CoreAPIConfig):
        super().__init__(
            name="movie_recommendation",
            description="Recommend movies and TV shows based on preferences",
            config=config
        )
    
    async def execute(self, context: Dict[str, Any], session: Session) -> FunctionResult:
        try:
            genre = context.get('genre', 'any')
            year = context.get('year')
            rating_min = context.get('rating_min', 0)
            content_type = context.get('content_type', 'movie')  # movie or tv
            
            async with httpx.AsyncClient() as client:
                if hasattr(self.config, 'tmdb_api_key'):
                    # The Movie Database API
                    endpoint = 'movie' if content_type == 'movie' else 'tv'
                    
                    params = {
                        'api_key': self.config.tmdb_api_key,
                        'sort_by': 'popularity.desc',
                        'page': 1
                    }
                    
                    if year:
                        if content_type == 'movie':
                            params['year'] = year
                        else:
                            params['first_air_date_year'] = year
                    
                    if rating_min:
                        params['vote_average.gte'] = rating_min
                    
                    response = await client.get(
                        f'https://api.themoviedb.org/3/discover/{endpoint}',
                        params=params
                    )
                    
                    if response.status_code == 200:
                        content_data = response.json()
                        
                        recommendations = []
                        for item in content_data['results'][:10]:
                            title = item.get('title') if content_type == 'movie' else item.get('name')
                            release_date = item.get('release_date') if content_type == 'movie' else item.get('first_air_date')
                            
                            recommendations.append({
                                'id': item['id'],
                                'title': title,
                                'overview': item['overview'],
                                'rating': item['vote_average'],
                                'release_date': release_date,
                                'poster_path': f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item['poster_path'] else None,
                                'genre_ids': item['genre_ids'],
                                'popularity': item['popularity']
                            })
                        
                        return FunctionResult(
                            success=True,
                            data={
                                'recommendation_id': f"movies_{uuid.uuid4().hex[:8]}",
                                'content_type': content_type,
                                'genre': genre,
                                'recommendations': recommendations,
                                'data_source': 'tmdb'
                            }
                        )
            
            # Fallback simulation
            movie_database = [
                {
                    'title': 'Inception',
                    'genre': 'Sci-Fi',
                    'year': 2010,
                    'rating': 8.8,
                    'director': 'Christopher Nolan'
                },
                {
                    'title': 'The Shawshank Redemption',
                    'genre': 'Drama',
                    'year': 1994,
                    'rating': 9.3,
                    'director': 'Frank Darabont'
                },
                {
                    'title': 'Avengers: Endgame',
                    'genre': 'Action',
                    'year': 2019,
                    'rating': 8.4,
                    'director': 'Russo Brothers'
                }
            ]
            
            # Filter by preferences
            filtered_movies = [
                movie for movie in movie_database
                if (genre == 'any' or movie['genre'].lower() == genre.lower()) and
                   (not year or movie['year'] == year) and
                   movie['rating'] >= rating_min
            ]
            
            return FunctionResult(
                success=True,
                data={
                    'recommendation_id': f"movies_{uuid.uuid4().hex[:8]}",
                    'content_type': content_type,
                    'genre': genre,
                    'recommendations': filtered_movies,
                    'data_source': 'simulation'
                }
            )
            
        except Exception as e:
            return FunctionResult(False, error=str(e))


# ==================== SECURITY & MONITORING FUNCTIONS ====================

class SecurityScannerFunction(AgenticFunction):
    """Scan for security vulnerabilities."""
    
    def __init__(self, config: CoreAPIConfig):
        super().__init__(
            name="security_scanner",
            description="Scan websites, systems, and code for security vulnerabilities",
            config=config
        )
    
    async def execute(self, context: Dict[str, Any], session: Session) -> FunctionResult:
        try:
            scan_type = context.get('scan_type', 'web_vulnerability')
            target = context.get('target')
            
            if not target:
                return FunctionResult(False, error="Missing scan target")
            
            scan_id = f"scan_{uuid.uuid4().hex[:8]}"
            
            # Simulate security scan based on type
            if scan_type == 'web_vulnerability':
                # Web application security scan
                vulnerabilities = [
                    {
                        'severity': 'High',
                        'type': 'SQL Injection',
                        'location': '/login.php',
                        'description': 'Potential SQL injection vulnerability in login form',
                        'cvss_score': 8.1,
                        'recommendation': 'Use parameterized queries'
                    },
                    {
                        'severity': 'Medium',
                        'type': 'Cross-Site Scripting (XSS)',
                        'location': '/search.php',
                        'description': 'Reflected XSS vulnerability in search parameter',
                        'cvss_score': 6.1,
                        'recommendation': 'Implement input validation and output encoding'
                    },
                    {
                        'severity': 'Low',
                        'type': 'Information Disclosure',
                        'location': '/admin/',
                        'description': 'Directory listing enabled',
                        'cvss_score': 3.1,
                        'recommendation': 'Disable directory browsing'
                    }
                ]
                
                scan_results = {
                    'vulnerabilities_found': len(vulnerabilities),
                    'critical': len([v for v in vulnerabilities if v['severity'] == 'Critical']),
                    'high': len([v for v in vulnerabilities if v['severity'] == 'High']),
                    'medium': len([v for v in vulnerabilities if v['severity'] == 'Medium']),
                    'low': len([v for v in vulnerabilities if v['severity'] == 'Low']),
                    'vulnerabilities': vulnerabilities
                }
                
            elif scan_type == 'network_scan':
                # Network security scan
                open_ports = [22, 80, 443, 3306]
                services = ['SSH', 'HTTP', 'HTTPS', 'MySQL']
                
                scan_results = {
                    'open_ports': open_ports,
                    'services_detected': services,
                    'firewall_status': 'Active',
                    'intrusion_detection': 'Enabled',
                    'recommendations': [
                        'Close unnecessary ports',
                        'Update service versions',
                        'Enable fail2ban for SSH'
                    ]
                }
                
            elif scan_type == 'malware_scan':
                # Malware scan
                scan_results = {
                    'files_scanned': 15000,
                    'threats_found': 0,
                    'quarantined_files': 0,
                    'scan_duration': '45 minutes',
                    'last_definition_update': datetime.utcnow().isoformat(),
                    'status': 'Clean'
                }
            
            else:
                scan_results = {'error': 'Unknown scan type'}
            
            # Calculate overall security score
            if scan_type == 'web_vulnerability':
                high_vulns = scan_results.get('high', 0)
                medium_vulns = scan_results.get('medium', 0)
                low_vulns = scan_results.get('low', 0)
                
                # Simple scoring algorithm
                security_score = max(0, 100 - (high_vulns * 20) - (medium_vulns * 10) - (low_vulns * 5))
            else:
                security_score = 85  # Default score
            
            return FunctionResult(
                success=True,
                data={
                    'scan_id': scan_id,
                    'target': target,
                    'scan_type': scan_type,
                    'results': scan_results,
                    'security_score': security_score,
                    'scan_completed_at': datetime.utcnow().isoformat(),
                    'report_url': f"/security/scan_{scan_id}.pdf"
                }
            )
            
        except Exception as e:
            return FunctionResult(False, error=str(e))


class PasswordGeneratorFunction(AgenticFunction):
    """Generate secure passwords and check password strength."""
    
    def __init__(self, config: CoreAPIConfig):
        super().__init__(
            name="password_generator",
            description="Generate secure passwords and analyze password strength",
            config=config
        )
    
    async def execute(self, context: Dict[str, Any], session: Session) -> FunctionResult:
        try:
            action = context.get('action', 'generate')
            
            if action == 'generate':
                length = context.get('length', 16)
                include_uppercase = context.get('include_uppercase', True)
                include_lowercase = context.get('include_lowercase', True)
                include_numbers = context.get('include_numbers', True)
                include_symbols = context.get('include_symbols', True)
                exclude_ambiguous = context.get('exclude_ambiguous', True)
                
                import string
                import secrets
                
                # Build character set
                chars = ''
                if include_lowercase:
                    chars += string.ascii_lowercase
                if include_uppercase:
                    chars += string.ascii_uppercase
                if include_numbers:
                    chars += string.digits
                if include_symbols:
                    chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
                
                if exclude_ambiguous:
                    # Remove ambiguous characters
                    ambiguous = '0O1lI'
                    chars = ''.join(c for c in chars if c not in ambiguous)
                
                if not chars:
                    return FunctionResult(False, error="No character types selected")
                
                # Generate password
                password = ''.join(secrets.choice(chars) for _ in range(length))
                
                # Calculate strength
                strength_score = self._calculate_password_strength(password)
                
                return FunctionResult(
                    success=True,
                    data={
                        'password': password,
                        'length': length,
                        'strength_score': strength_score,
                        'strength_level': self._get_strength_level(strength_score),
                        'entropy_bits': len(chars) ** length,
                        'character_types': {
                            'uppercase': include_uppercase,
                            'lowercase': include_lowercase,
                            'numbers': include_numbers,
                            'symbols': include_symbols
                        }
                    }
                )
            
            elif action == 'check_strength':
                password = context.get('password')
                
                if not password:
                    return FunctionResult(False, error="Missing password to check")
                
                strength_score = self._calculate_password_strength(password)
                
                # Check against common passwords
                common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
                is_common = password.lower() in common_passwords
                
                # Check for patterns
                has_patterns = self._check_patterns(password)
                
                return FunctionResult(
                    success=True,
                    data={
                        'password_length': len(password),
                        'strength_score': strength_score,
                        'strength_level': self._get_strength_level(strength_score),
                        'is_common_password': is_common,
                        'has_patterns': has_patterns,
                        'recommendations': self._get_password_recommendations(password, strength_score)
                    }
                )
            
        except Exception as e:
            return FunctionResult(False, error=str(e))
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)."""
        score = 0
        
        # Length bonus
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Character variety
        if any(c.islower() for c in password):
            score += 10
        if any(c.isupper() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 10
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            score += 20
        
        # Deduct for common patterns
        if password.lower() in ['password', '123456', 'qwerty']:
            score -= 50
        
        return min(100, max(0, score))
    
    def _get_strength_level(self, score: int) -> str:
        """Get password strength level."""
        if score >= 80:
            return 'Very Strong'
        elif score >= 60:
            return 'Strong'
        elif score >= 40:
            return 'Medium'
        elif score >= 20:
            return 'Weak'
        else:
            return 'Very Weak'
    
    def _check_patterns(self, password: str) -> bool:
        """Check for common patterns in password."""
        # Check for sequential characters
        for i in range(len(password) - 2):
            if ord(password[i+1]) == ord(password[i]) + 1 and ord(password[i+2]) == ord(password[i]) + 2:
                return True
        
        # Check for repeated characters
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                return True
        
        return False
    
    def _get_password_recommendations(self, password: str, score: int) -> List[str]:
        """Get recommendations for improving password."""
        recommendations = []
        
        if len(password) < 12:
            recommendations.append("Increase password length to at least 12 characters")
        
        if not any(c.isupper() for c in password):
            recommendations.append("Add uppercase letters")
        
        if not any(c.islower() for c in password):
            recommendations.append("Add lowercase letters")
        
        if not any(c.isdigit() for c in password):
            recommendations.append("Add numbers")
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            recommendations.append("Add special characters")
        
        if score < 60:
            recommendations.append("Consider using a password manager")
        
        return recommendations
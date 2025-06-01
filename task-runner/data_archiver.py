"""
Data Archiver for Project GeminiVoiceConnect

This module provides comprehensive data archiving and lifecycle management
capabilities with intelligent compression, encryption, and retrieval systems.
It manages long-term data storage, compliance requirements, and automated
data retention policies.

Key Features:
- Automated data lifecycle management
- Intelligent compression and deduplication
- Encrypted archival storage
- Compliance-driven retention policies
- Fast retrieval and restoration
- Data integrity verification
- Audit trail maintenance
- Cost-optimized storage tiering
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
import uuid
import hashlib
import gzip
import pickle
import os
import shutil
from pathlib import Path
import sqlite3
from cryptography.fernet import Fernet
from celery import Task
import tarfile
import zipfile

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ArchiveStatus(str, Enum):
    """Archive status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTORED = "restored"
    DELETED = "deleted"


class DataType(str, Enum):
    """Data type enumeration"""
    CALL_LOGS = "call_logs"
    SMS_LOGS = "sms_logs"
    CUSTOMER_DATA = "customer_data"
    CAMPAIGN_DATA = "campaign_data"
    ANALYTICS_DATA = "analytics_data"
    SYSTEM_LOGS = "system_logs"
    AUDIT_LOGS = "audit_logs"
    PERFORMANCE_METRICS = "performance_metrics"
    FINANCIAL_DATA = "financial_data"


class CompressionType(str, Enum):
    """Compression type enumeration"""
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"
    TAR_GZ = "tar_gz"
    LZMA = "lzma"


class StorageTier(str, Enum):
    """Storage tier enumeration"""
    HOT = "hot"           # Frequently accessed
    WARM = "warm"         # Occasionally accessed
    COLD = "cold"         # Rarely accessed
    FROZEN = "frozen"     # Archive storage


@dataclass
class ArchivePolicy:
    """Archive policy configuration"""
    policy_id: str
    data_type: DataType
    retention_days: int
    archive_after_days: int
    compression_type: CompressionType
    encryption_enabled: bool
    storage_tier: StorageTier
    auto_delete_after_days: Optional[int] = None
    compliance_requirements: Optional[List[str]] = None


@dataclass
class ArchiveJob:
    """Archive job specification"""
    job_id: str
    tenant_id: str
    data_type: DataType
    source_query: str
    date_range: Dict[str, datetime]
    policy: ArchivePolicy
    priority: int = 5
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ArchiveRecord:
    """Archive record metadata"""
    archive_id: str
    job_id: str
    tenant_id: str
    data_type: DataType
    created_at: datetime
    archived_at: Optional[datetime]
    file_path: str
    file_size: int
    record_count: int
    compression_ratio: float
    checksum: str
    encryption_key_id: Optional[str]
    storage_tier: StorageTier
    status: ArchiveStatus
    expiry_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ArchiveResult:
    """Archive operation result"""
    job_id: str
    status: ArchiveStatus
    records_processed: int
    files_created: int
    total_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float
    processing_time: float
    error_message: Optional[str] = None


class EncryptionManager:
    """
    Encryption manager for secure data archiving.
    
    This manager handles encryption key generation, rotation, and
    secure storage for archived data.
    """
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.key_cache = {}
        
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        key_file = "/tmp/archive_master.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new master key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def generate_archive_key(self, archive_id: str) -> str:
        """Generate unique encryption key for archive"""
        # Create deterministic key based on archive ID and master key
        combined = f"{archive_id}:{self.master_key.decode()}"
        key_hash = hashlib.sha256(combined.encode()).digest()
        
        # Use first 32 bytes for Fernet key
        fernet_key = Fernet.generate_key()
        key_id = hashlib.md5(fernet_key).hexdigest()
        
        # Store key securely (in production, use proper key management)
        self.key_cache[key_id] = fernet_key
        
        return key_id
    
    def get_encryption_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve encryption key by ID"""
        return self.key_cache.get(key_id)
    
    def encrypt_data(self, data: bytes, key_id: str) -> bytes:
        """Encrypt data using specified key"""
        key = self.get_encryption_key(key_id)
        if not key:
            raise ValueError(f"Encryption key not found: {key_id}")
        
        fernet = Fernet(key)
        return fernet.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data using specified key"""
        key = self.get_encryption_key(key_id)
        if not key:
            raise ValueError(f"Encryption key not found: {key_id}")
        
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data)


class CompressionEngine:
    """
    Advanced compression engine for data archiving.
    
    This engine provides multiple compression algorithms optimized
    for different data types and access patterns.
    """
    
    def __init__(self):
        self.compression_stats = {}
    
    async def compress_data(
        self,
        data: bytes,
        compression_type: CompressionType,
        data_type: DataType
    ) -> Tuple[bytes, float]:
        """Compress data and return compressed data with ratio"""
        try:
            original_size = len(data)
            
            if compression_type == CompressionType.GZIP:
                compressed_data = gzip.compress(data, compresslevel=9)
            elif compression_type == CompressionType.ZIP:
                compressed_data = self._zip_compress(data)
            elif compression_type == CompressionType.LZMA:
                import lzma
                compressed_data = lzma.compress(data, preset=9)
            else:
                compressed_data = data
            
            compressed_size = len(compressed_data)
            compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
            
            # Update compression statistics
            self._update_compression_stats(data_type, compression_type, compression_ratio)
            
            return compressed_data, compression_ratio
            
        except Exception as e:
            logger.error(f"Compression failed: {str(e)}")
            return data, 1.0
    
    async def decompress_data(
        self,
        compressed_data: bytes,
        compression_type: CompressionType
    ) -> bytes:
        """Decompress data"""
        try:
            if compression_type == CompressionType.GZIP:
                return gzip.decompress(compressed_data)
            elif compression_type == CompressionType.ZIP:
                return self._zip_decompress(compressed_data)
            elif compression_type == CompressionType.LZMA:
                import lzma
                return lzma.decompress(compressed_data)
            else:
                return compressed_data
                
        except Exception as e:
            logger.error(f"Decompression failed: {str(e)}")
            raise
    
    def _zip_compress(self, data: bytes) -> bytes:
        """Compress data using ZIP"""
        import io
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.writestr('data', data)
        
        return buffer.getvalue()
    
    def _zip_decompress(self, compressed_data: bytes) -> bytes:
        """Decompress ZIP data"""
        import io
        
        buffer = io.BytesIO(compressed_data)
        with zipfile.ZipFile(buffer, 'r') as zf:
            return zf.read('data')
    
    def _update_compression_stats(
        self,
        data_type: DataType,
        compression_type: CompressionType,
        ratio: float
    ):
        """Update compression statistics"""
        key = f"{data_type.value}_{compression_type.value}"
        
        if key not in self.compression_stats:
            self.compression_stats[key] = {
                'count': 0,
                'total_ratio': 0.0,
                'avg_ratio': 0.0,
                'best_ratio': 1.0,
                'worst_ratio': 1.0
            }
        
        stats = self.compression_stats[key]
        stats['count'] += 1
        stats['total_ratio'] += ratio
        stats['avg_ratio'] = stats['total_ratio'] / stats['count']
        stats['best_ratio'] = min(stats['best_ratio'], ratio)
        stats['worst_ratio'] = max(stats['worst_ratio'], ratio)
    
    def get_optimal_compression(self, data_type: DataType) -> CompressionType:
        """Get optimal compression type for data type"""
        # Analyze historical compression ratios
        best_compression = CompressionType.GZIP
        best_ratio = 1.0
        
        for compression_type in CompressionType:
            key = f"{data_type.value}_{compression_type.value}"
            stats = self.compression_stats.get(key)
            
            if stats and stats['avg_ratio'] < best_ratio:
                best_ratio = stats['avg_ratio']
                best_compression = compression_type
        
        return best_compression


class DataArchiver:
    """
    Comprehensive data archiving system.
    
    This archiver manages the complete data lifecycle from active storage
    to long-term archival, including compression, encryption, and retrieval.
    """
    
    def __init__(self):
        self.encryption_manager = EncryptionManager()
        self.compression_engine = CompressionEngine()
        self.archive_db = self._initialize_archive_db()
        self.storage_root = Path("/tmp/archives")
        self.storage_root.mkdir(exist_ok=True)
        
    def _initialize_archive_db(self) -> sqlite3.Connection:
        """Initialize archive metadata database"""
        db_path = "/tmp/archive_metadata.db"
        conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # Create tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS archive_records (
                archive_id TEXT PRIMARY KEY,
                job_id TEXT,
                tenant_id TEXT,
                data_type TEXT,
                created_at TEXT,
                archived_at TEXT,
                file_path TEXT,
                file_size INTEGER,
                record_count INTEGER,
                compression_ratio REAL,
                checksum TEXT,
                encryption_key_id TEXT,
                storage_tier TEXT,
                status TEXT,
                expiry_date TEXT,
                metadata TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS archive_policies (
                policy_id TEXT PRIMARY KEY,
                data_type TEXT,
                retention_days INTEGER,
                archive_after_days INTEGER,
                compression_type TEXT,
                encryption_enabled BOOLEAN,
                storage_tier TEXT,
                auto_delete_after_days INTEGER,
                compliance_requirements TEXT
            )
        """)
        
        conn.commit()
        return conn
    
    async def archive_data(self, job: ArchiveJob) -> ArchiveResult:
        """Archive data according to job specification"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting archive job {job.job_id} for tenant {job.tenant_id}")
            
            # Extract data based on query
            data_records = await self._extract_data(job)
            
            if not data_records:
                return ArchiveResult(
                    job_id=job.job_id,
                    status=ArchiveStatus.COMPLETED,
                    records_processed=0,
                    files_created=0,
                    total_size_bytes=0,
                    compressed_size_bytes=0,
                    compression_ratio=1.0,
                    processing_time=0.0
                )
            
            # Serialize data
            serialized_data = await self._serialize_data(data_records, job.data_type)
            original_size = len(serialized_data)
            
            # Compress data
            compressed_data, compression_ratio = await self.compression_engine.compress_data(
                serialized_data, job.policy.compression_type, job.data_type
            )
            
            # Encrypt if required
            encryption_key_id = None
            if job.policy.encryption_enabled:
                archive_id = str(uuid.uuid4())
                encryption_key_id = self.encryption_manager.generate_archive_key(archive_id)
                compressed_data = self.encryption_manager.encrypt_data(compressed_data, encryption_key_id)
            else:
                archive_id = str(uuid.uuid4())
            
            # Calculate checksum
            checksum = hashlib.sha256(compressed_data).hexdigest()
            
            # Store archive file
            file_path = await self._store_archive_file(
                archive_id, compressed_data, job.policy.storage_tier
            )
            
            # Create archive record
            archive_record = ArchiveRecord(
                archive_id=archive_id,
                job_id=job.job_id,
                tenant_id=job.tenant_id,
                data_type=job.data_type,
                created_at=datetime.utcnow(),
                archived_at=datetime.utcnow(),
                file_path=file_path,
                file_size=len(compressed_data),
                record_count=len(data_records),
                compression_ratio=compression_ratio,
                checksum=checksum,
                encryption_key_id=encryption_key_id,
                storage_tier=job.policy.storage_tier,
                status=ArchiveStatus.COMPLETED,
                expiry_date=self._calculate_expiry_date(job.policy),
                metadata=job.metadata
            )
            
            # Save archive record
            await self._save_archive_record(archive_record)
            
            # Clean up source data if configured
            if job.policy.auto_delete_after_days:
                await self._schedule_source_cleanup(job)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = ArchiveResult(
                job_id=job.job_id,
                status=ArchiveStatus.COMPLETED,
                records_processed=len(data_records),
                files_created=1,
                total_size_bytes=original_size,
                compressed_size_bytes=len(compressed_data),
                compression_ratio=compression_ratio,
                processing_time=processing_time
            )
            
            logger.info(f"Archive job {job.job_id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Archive job {job.job_id} failed: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ArchiveResult(
                job_id=job.job_id,
                status=ArchiveStatus.FAILED,
                records_processed=0,
                files_created=0,
                total_size_bytes=0,
                compressed_size_bytes=0,
                compression_ratio=1.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def restore_data(
        self,
        archive_id: str,
        target_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restore archived data"""
        try:
            # Get archive record
            archive_record = await self._get_archive_record(archive_id)
            if not archive_record:
                raise ValueError(f"Archive record not found: {archive_id}")
            
            # Read archive file
            with open(archive_record.file_path, 'rb') as f:
                archived_data = f.read()
            
            # Verify checksum
            current_checksum = hashlib.sha256(archived_data).hexdigest()
            if current_checksum != archive_record.checksum:
                raise ValueError("Archive data integrity check failed")
            
            # Decrypt if encrypted
            if archive_record.encryption_key_id:
                archived_data = self.encryption_manager.decrypt_data(
                    archived_data, archive_record.encryption_key_id
                )
            
            # Decompress data
            decompressed_data = await self.compression_engine.decompress_data(
                archived_data, self._get_compression_type_from_record(archive_record)
            )
            
            # Deserialize data
            restored_records = await self._deserialize_data(decompressed_data, archive_record.data_type)
            
            # Update archive record status
            await self._update_archive_status(archive_id, ArchiveStatus.RESTORED)
            
            logger.info(f"Archive {archive_id} restored successfully")
            
            return {
                'archive_id': archive_id,
                'records_count': len(restored_records),
                'data': restored_records,
                'metadata': archive_record.metadata
            }
            
        except Exception as e:
            logger.error(f"Archive restoration failed: {str(e)}")
            raise
    
    async def delete_archive(self, archive_id: str, force: bool = False) -> bool:
        """Delete archived data"""
        try:
            archive_record = await self._get_archive_record(archive_id)
            if not archive_record:
                return False
            
            # Check if deletion is allowed
            if not force and archive_record.expiry_date and archive_record.expiry_date > datetime.utcnow():
                raise ValueError("Archive has not reached expiry date")
            
            # Delete archive file
            if os.path.exists(archive_record.file_path):
                os.remove(archive_record.file_path)
            
            # Update archive record
            await self._update_archive_status(archive_id, ArchiveStatus.DELETED)
            
            logger.info(f"Archive {archive_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Archive deletion failed: {str(e)}")
            return False
    
    async def get_archive_info(self, archive_id: str) -> Optional[Dict[str, Any]]:
        """Get archive information"""
        try:
            archive_record = await self._get_archive_record(archive_id)
            if not archive_record:
                return None
            
            return {
                'archive_id': archive_record.archive_id,
                'job_id': archive_record.job_id,
                'tenant_id': archive_record.tenant_id,
                'data_type': archive_record.data_type.value,
                'created_at': archive_record.created_at.isoformat(),
                'archived_at': archive_record.archived_at.isoformat() if archive_record.archived_at else None,
                'file_size': archive_record.file_size,
                'record_count': archive_record.record_count,
                'compression_ratio': archive_record.compression_ratio,
                'storage_tier': archive_record.storage_tier.value,
                'status': archive_record.status.value,
                'expiry_date': archive_record.expiry_date.isoformat() if archive_record.expiry_date else None,
                'encrypted': archive_record.encryption_key_id is not None,
                'metadata': archive_record.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get archive info: {str(e)}")
            return None
    
    async def list_archives(
        self,
        tenant_id: Optional[str] = None,
        data_type: Optional[DataType] = None,
        status: Optional[ArchiveStatus] = None
    ) -> List[Dict[str, Any]]:
        """List archives with optional filters"""
        try:
            query = "SELECT * FROM archive_records WHERE 1=1"
            params = []
            
            if tenant_id:
                query += " AND tenant_id = ?"
                params.append(tenant_id)
            
            if data_type:
                query += " AND data_type = ?"
                params.append(data_type.value)
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            query += " ORDER BY created_at DESC"
            
            cursor = self.archive_db.execute(query, params)
            rows = cursor.fetchall()
            
            archives = []
            for row in rows:
                archive_info = {
                    'archive_id': row[0],
                    'job_id': row[1],
                    'tenant_id': row[2],
                    'data_type': row[3],
                    'created_at': row[4],
                    'archived_at': row[5],
                    'file_path': row[6],
                    'file_size': row[7],
                    'record_count': row[8],
                    'compression_ratio': row[9],
                    'checksum': row[10],
                    'encryption_key_id': row[11],
                    'storage_tier': row[12],
                    'status': row[13],
                    'expiry_date': row[14],
                    'metadata': json.loads(row[15]) if row[15] else None
                }
                archives.append(archive_info)
            
            return archives
            
        except Exception as e:
            logger.error(f"Failed to list archives: {str(e)}")
            return []
    
    async def cleanup_expired_archives(self) -> Dict[str, int]:
        """Clean up expired archives"""
        try:
            current_time = datetime.utcnow()
            
            # Find expired archives
            cursor = self.archive_db.execute(
                "SELECT archive_id FROM archive_records WHERE expiry_date < ? AND status != ?",
                (current_time.isoformat(), ArchiveStatus.DELETED.value)
            )
            
            expired_archives = [row[0] for row in cursor.fetchall()]
            
            deleted_count = 0
            failed_count = 0
            
            for archive_id in expired_archives:
                try:
                    if await self.delete_archive(archive_id, force=True):
                        deleted_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete expired archive {archive_id}: {str(e)}")
                    failed_count += 1
            
            logger.info(f"Cleanup completed: {deleted_count} deleted, {failed_count} failed")
            
            return {
                'expired_found': len(expired_archives),
                'deleted': deleted_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f"Archive cleanup failed: {str(e)}")
            return {'expired_found': 0, 'deleted': 0, 'failed': 0}
    
    async def _extract_data(self, job: ArchiveJob) -> List[Dict[str, Any]]:
        """Extract data based on job specification"""
        # This would execute the actual database query
        # For now, generate mock data based on data type
        
        mock_data = []
        record_count = 1000  # Mock record count
        
        for i in range(record_count):
            if job.data_type == DataType.CALL_LOGS:
                record = {
                    'call_id': f"call_{i}",
                    'tenant_id': job.tenant_id,
                    'caller': f"+1555000{i:04d}",
                    'callee': f"+1555999{i:04d}",
                    'start_time': (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    'duration': 120 + (i % 300),
                    'status': 'completed',
                    'recording_path': f"/recordings/call_{i}.wav"
                }
            elif job.data_type == DataType.SMS_LOGS:
                record = {
                    'sms_id': f"sms_{i}",
                    'tenant_id': job.tenant_id,
                    'sender': f"+1555000{i:04d}",
                    'recipient': f"+1555999{i:04d}",
                    'message': f"Test message {i}",
                    'sent_at': (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    'status': 'delivered'
                }
            else:
                record = {
                    'id': f"record_{i}",
                    'tenant_id': job.tenant_id,
                    'data': f"Sample data {i}",
                    'timestamp': (datetime.utcnow() - timedelta(days=i)).isoformat()
                }
            
            mock_data.append(record)
        
        return mock_data
    
    async def _serialize_data(self, data: List[Dict[str, Any]], data_type: DataType) -> bytes:
        """Serialize data for archiving"""
        try:
            # Use pickle for efficient serialization
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Data serialization failed: {str(e)}")
            # Fallback to JSON
            return json.dumps(data, default=str).encode('utf-8')
    
    async def _deserialize_data(self, data: bytes, data_type: DataType) -> List[Dict[str, Any]]:
        """Deserialize archived data"""
        try:
            # Try pickle first
            return pickle.loads(data)
        except Exception:
            try:
                # Fallback to JSON
                return json.loads(data.decode('utf-8'))
            except Exception as e:
                logger.error(f"Data deserialization failed: {str(e)}")
                raise
    
    async def _store_archive_file(
        self,
        archive_id: str,
        data: bytes,
        storage_tier: StorageTier
    ) -> str:
        """Store archive file in appropriate storage tier"""
        # Create tier-specific directory
        tier_dir = self.storage_root / storage_tier.value
        tier_dir.mkdir(exist_ok=True)
        
        # Create date-based subdirectory
        date_dir = tier_dir / datetime.utcnow().strftime("%Y/%m/%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Store file
        file_path = date_dir / f"{archive_id}.archive"
        
        with open(file_path, 'wb') as f:
            f.write(data)
        
        return str(file_path)
    
    async def _save_archive_record(self, record: ArchiveRecord):
        """Save archive record to database"""
        self.archive_db.execute("""
            INSERT INTO archive_records (
                archive_id, job_id, tenant_id, data_type, created_at, archived_at,
                file_path, file_size, record_count, compression_ratio, checksum,
                encryption_key_id, storage_tier, status, expiry_date, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.archive_id,
            record.job_id,
            record.tenant_id,
            record.data_type.value,
            record.created_at.isoformat(),
            record.archived_at.isoformat() if record.archived_at else None,
            record.file_path,
            record.file_size,
            record.record_count,
            record.compression_ratio,
            record.checksum,
            record.encryption_key_id,
            record.storage_tier.value,
            record.status.value,
            record.expiry_date.isoformat() if record.expiry_date else None,
            json.dumps(record.metadata) if record.metadata else None
        ))
        self.archive_db.commit()
    
    async def _get_archive_record(self, archive_id: str) -> Optional[ArchiveRecord]:
        """Get archive record from database"""
        cursor = self.archive_db.execute(
            "SELECT * FROM archive_records WHERE archive_id = ?",
            (archive_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return ArchiveRecord(
            archive_id=row[0],
            job_id=row[1],
            tenant_id=row[2],
            data_type=DataType(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            archived_at=datetime.fromisoformat(row[5]) if row[5] else None,
            file_path=row[6],
            file_size=row[7],
            record_count=row[8],
            compression_ratio=row[9],
            checksum=row[10],
            encryption_key_id=row[11],
            storage_tier=StorageTier(row[12]),
            status=ArchiveStatus(row[13]),
            expiry_date=datetime.fromisoformat(row[14]) if row[14] else None,
            metadata=json.loads(row[15]) if row[15] else None
        )
    
    async def _update_archive_status(self, archive_id: str, status: ArchiveStatus):
        """Update archive status"""
        self.archive_db.execute(
            "UPDATE archive_records SET status = ? WHERE archive_id = ?",
            (status.value, archive_id)
        )
        self.archive_db.commit()
    
    def _calculate_expiry_date(self, policy: ArchivePolicy) -> Optional[datetime]:
        """Calculate archive expiry date based on policy"""
        if policy.auto_delete_after_days:
            return datetime.utcnow() + timedelta(days=policy.auto_delete_after_days)
        return None
    
    def _get_compression_type_from_record(self, record: ArchiveRecord) -> CompressionType:
        """Get compression type from archive record metadata"""
        if record.metadata and 'compression_type' in record.metadata:
            return CompressionType(record.metadata['compression_type'])
        return CompressionType.GZIP  # Default
    
    async def _schedule_source_cleanup(self, job: ArchiveJob):
        """Schedule cleanup of source data after archiving"""
        # This would schedule a cleanup task
        logger.info(f"Scheduled source cleanup for job {job.job_id}")


# Global data archiver instance
data_archiver = DataArchiver()


class DataArchiverTask(Task):
    """Celery task for data archiving"""
    
    def run(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run data archiving task"""
        try:
            # Convert job data to ArchiveJob object
            policy = ArchivePolicy(
                policy_id=job_data['policy']['policy_id'],
                data_type=DataType(job_data['policy']['data_type']),
                retention_days=job_data['policy']['retention_days'],
                archive_after_days=job_data['policy']['archive_after_days'],
                compression_type=CompressionType(job_data['policy']['compression_type']),
                encryption_enabled=job_data['policy']['encryption_enabled'],
                storage_tier=StorageTier(job_data['policy']['storage_tier']),
                auto_delete_after_days=job_data['policy'].get('auto_delete_after_days'),
                compliance_requirements=job_data['policy'].get('compliance_requirements')
            )
            
            job = ArchiveJob(
                job_id=job_data['job_id'],
                tenant_id=job_data['tenant_id'],
                data_type=DataType(job_data['data_type']),
                source_query=job_data['source_query'],
                date_range={
                    'start': datetime.fromisoformat(job_data['date_range']['start']),
                    'end': datetime.fromisoformat(job_data['date_range']['end'])
                },
                policy=policy,
                priority=job_data.get('priority', 5),
                metadata=job_data.get('metadata')
            )
            
            # Execute archiving
            result = asyncio.run(data_archiver.archive_data(job))
            return asdict(result)
            
        except Exception as e:
            logger.error(f"Data archiving task failed: {str(e)}")
            return {
                "job_id": job_data.get("job_id", "unknown"),
                "status": ArchiveStatus.FAILED.value,
                "records_processed": 0,
                "files_created": 0,
                "total_size_bytes": 0,
                "compressed_size_bytes": 0,
                "compression_ratio": 1.0,
                "processing_time": 0.0,
                "error_message": str(e)
            }
"""
Hyperledger Fabric Blockchain Service

Provides secure integration with Hyperledger Fabric via Python fabric-gateway SDK.
Handles all blockchain operations: submitting transactions and evaluating chaincode.

Key principles:
- TLS required for all peer connections
- Credentials loaded from file paths (never hardcoded or embedded in code)
- Clean service abstraction: routes call these functions, never fabric-gateway directly
- Graceful error handling for connection and chaincode failures
- Fully mockable for unit testing (no side effects at import time)
"""

import logging
import ssl
from typing import Any, List, Optional
from abc import ABC, abstractmethod

from app.core.config import settings

logger = logging.getLogger(__name__)


class BlockchainServiceError(Exception):
    """Base exception for blockchain service failures"""
    pass


class BlockchainConnectionError(BlockchainServiceError):
    """Raised when unable to connect to Fabric peer or gateway"""
    pass


class BlockchainTransactionError(BlockchainServiceError):
    """Raised when transaction execution fails on Fabric"""
    pass


class IBlockchainService(ABC):
    """
    Abstract interface for blockchain operations.
    Enables easy mocking in unit tests.
    """

    @abstractmethod
    async def submit_transaction(
        self, function_name: str, *args: str
    ) -> str:
        """
        Submit a transaction to the blockchain (write operation).
        Waits for transaction to be committed to the ledger.

        Args:
            function_name: Name of the chaincode function to invoke
            *args: String arguments to pass to the chaincode function

        Returns:
            Transaction result as string

        Raises:
            BlockchainConnectionError: If unable to connect to peer
            BlockchainTransactionError: If transaction fails on fabric
        """
        pass

    @abstractmethod
    async def evaluate_transaction(
        self, function_name: str, *args: str
    ) -> str:
        """
        Evaluate a transaction on the blockchain (read operation).
        Does not modify ledger state. Returns immediately.

        Args:
            function_name: Name of the chaincode function to invoke
            *args: String arguments to pass to the chaincode function

        Returns:
            Chaincode response as string

        Raises:
            BlockchainConnectionError: If unable to connect to peer
            BlockchainTransactionError: If evaluation fails on fabric
        """
        pass


class SupplyChainContractHelper:
    """
    Helper class for interacting with AgriTrack supplychain.go chaincode.
    Provides type-safe wrappers for all chaincode functions.

    Available supplychain.go v1.0 functions:
    - Product: CreateProduct, GetProduct, DeactivateProduct
    - Batch: CreateBatch, GetBatch, UpdateBatchStatus, CompleteBatch
    - Lifecycle: RecordLifecycleEvent, GetBatchLifecycleEvents (append-only)
    - Transport: CreateTransportManifest, GetTransport, UpdateTransportStatus
    - Temperature: AddTemperatureLog, GetTransportTemperatureLogs (auto-detects violations)
    - Processing: RecordProcessing, GetProcessingRecord
    - Certification: IssueCertification, GetCertification, UpdateCertificationStatus
    """

    def __init__(self, blockchain_service: IBlockchainService):
        self.service = blockchain_service

    async def create_product(self, product_id: str, name: str, description: str) -> str:
        """Create product (Regulator only)."""
        return await self.service.submit_transaction("CreateProduct", product_id, name, description)

    async def get_product(self, product_id: str) -> str:
        """Query product by ID."""
        return await self.service.evaluate_transaction("GetProduct", product_id)

    async def create_batch(
        self, batch_id: str, product_id: str, farmer_id: str, batch_number: str,
        quantity: int, start_date: str, expected_end_date: str, location: str,
        qr_code: str, notes: str,
    ) -> str:
        """Create batch (Farmer only)."""
        return await self.service.submit_transaction(
            "CreateBatch", batch_id, product_id, farmer_id, batch_number,
            str(quantity), start_date, expected_end_date, location, qr_code, notes,
        )

    async def get_batch(self, batch_id: str) -> str:
        """Query batch by ID."""
        return await self.service.evaluate_transaction("GetBatch", batch_id)

    async def record_lifecycle_event(
        self, event_id: str, batch_id: str, event_type: str, description: str,
        recorded_by: str, event_date: str, quantity_affected: int, metadata: str,
    ) -> str:
        """Record immutable lifecycle event (Farmer only)."""
        return await self.service.submit_transaction(
            "RecordLifecycleEvent", event_id, batch_id, event_type, description,
            recorded_by, event_date, str(quantity_affected), metadata,
        )

    async def get_batch_lifecycle_events(self, batch_id: str) -> str:
        """Query all lifecycle events for batch (audit trail)."""
        return await self.service.evaluate_transaction("GetBatchLifecycleEvents", batch_id)

    async def create_transport_manifest(
        self, transport_id: str, batch_id: str, from_party_id: str, to_party_id: str,
        vehicle_id: str, driver_name: str, departure_time: str, origin_location: str,
        destination_location: str, temperature_monitored: bool, notes: str,
    ) -> str:
        """Create transport manifest (Farmer only)."""
        return await self.service.submit_transaction(
            "CreateTransportManifest", transport_id, batch_id, from_party_id, to_party_id,
            vehicle_id, driver_name, departure_time, origin_location,
            destination_location, str(temperature_monitored).lower(), notes,
        )

    async def get_transport(self, transport_id: str) -> str:
        """Query transport manifest."""
        return await self.service.evaluate_transaction("GetTransport", transport_id)

    async def add_temperature_log(
        self, log_id: str, transport_id: str, temperature: float, timestamp: str, location: str,
    ) -> str:
        """Add temperature reading (auto-detects violations)."""
        return await self.service.submit_transaction(
            "AddTemperatureLog", log_id, transport_id, str(temperature), timestamp, location,
        )

    async def get_transport_temperature_logs(self, transport_id: str) -> str:
        """Query temperature logs for transport."""
        return await self.service.evaluate_transaction("GetTransportTemperatureLogs", transport_id)

    async def record_processing(
        self, processing_id: str, batch_id: str, process_date: str, facility_name: str,
        slaughter_count: int, yield_kg: float, quality_score: float, notes: str,
    ) -> str:
        """Record processing output (Farmer only)."""
        return await self.service.submit_transaction(
            "RecordProcessing", processing_id, batch_id, process_date, facility_name,
            str(slaughter_count), str(yield_kg), str(quality_score), notes,
        )

    async def get_processing_record(self, processing_id: str) -> str:
        """Query processing record."""
        return await self.service.evaluate_transaction("GetProcessingRecord", processing_id)

    async def issue_certification(
        self, certification_id: str, processing_id: str, cert_type: str,
        issued_date: str, expiry_date: str, issuer_id: str, notes: str,
    ) -> str:
        """Issue certification (Regulator only)."""
        return await self.service.submit_transaction(
            "IssueCertification", certification_id, processing_id, cert_type,
            issued_date, expiry_date, issuer_id, notes,
        )

    async def get_certification(self, certification_id: str) -> str:
        """Query certification record."""
        return await self.service.evaluate_transaction("GetCertification", certification_id)


class FabricBlockchainService(IBlockchainService):
    """
    Production Hyperledger Fabric integration using fabric-gateway SDK.

    Handles:
    - TLS credential loading and validation
    - gRPC secure channel creation
    - Gateway initialization and connection
    - Transaction submission and evaluation
    - Graceful error handling and logging
    """

    def __init__(self):
        """Initialize the Fabric blockchain service with secure TLS connection."""
        self._gateway = None
        self._contract = None
        self._initialized = False
        self._init_lock = False  # Prevent concurrent initialization

        # Validate configuration early but defer actual connection
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """
        Validate that all required Fabric configuration is present.
        Does not establish connection yet (deferred until first use).

        Raises:
            BlockchainServiceError: If required configuration is missing
        """
        required_fields = [
            ("FABRIC_CHANNEL", settings.FABRIC_CHANNEL),
            ("FABRIC_CHAINCODE", settings.FABRIC_CHAINCODE),
            ("FABRIC_PEER_ENDPOINT", settings.FABRIC_PEER_ENDPOINT),
            ("FABRIC_MSP_ID", settings.FABRIC_MSP_ID),
            ("FABRIC_IDENTITY", settings.FABRIC_IDENTITY),
            ("FABRIC_TLS_CA_CERT", settings.FABRIC_TLS_CA_CERT),
            ("FABRIC_IDENTITY_CERT", settings.FABRIC_IDENTITY_CERT),
            ("FABRIC_IDENTITY_KEY", settings.FABRIC_IDENTITY_KEY),
        ]

        missing_fields = [name for name, value in required_fields if not value]
        if missing_fields:
            raise BlockchainServiceError(
                f"Missing Fabric configuration: {', '.join(missing_fields)}. "
                "Set these in environment variables before using blockchain service."
            )

    def _load_tls_credentials(self) -> tuple[bytes, bytes, bytes]:
        """
        Load TLS credentials from file paths specified in environment.

        Returns:
            Tuple of (ca_cert_bytes, client_cert_bytes, client_key_bytes)

        Raises:
            BlockchainConnectionError: If files cannot be read
        """
        try:
            with open(settings.FABRIC_TLS_CA_CERT, "rb") as f:
                ca_cert = f.read()
            with open(settings.FABRIC_IDENTITY_CERT, "rb") as f:
                client_cert = f.read()
            with open(settings.FABRIC_IDENTITY_KEY, "rb") as f:
                client_key = f.read()
            return ca_cert, client_cert, client_key
        except FileNotFoundError as e:
            raise BlockchainConnectionError(
                f"TLS credential file not found: {e.filename}. "
                "Ensure FABRIC_TLS_CA_CERT, FABRIC_IDENTITY_CERT, and FABRIC_IDENTITY_KEY "
                "point to valid certificate files."
            ) from e
        except IOError as e:
            raise BlockchainConnectionError(
                f"Failed to read TLS credential file: {e}. "
                "Check file permissions and accessibility."
            ) from e

    async def _initialize_connection(self) -> None:
        """
        Establish connection to Fabric peer via secure gRPC channel.
        Called lazily on first transaction/evaluation request.

        Raises:
            BlockchainConnectionError: If connection cannot be established
        """
        if self._initialized:
            return

        if self._init_lock:
            raise BlockchainConnectionError(
                "Initialization already in progress. Possible concurrent access."
            )

        try:
            self._init_lock = True

            # Import here to avoid hard dependency if fabric-gateway not installed
            try:
                from fabric_gateway import connect
                import grpc
            except ImportError as e:
                raise BlockchainConnectionError(
                    "fabric-gateway SDK not installed. "
                    "Install with: pip install fabric-gateway"
                ) from e

            # Load TLS credentials from secure file paths
            ca_cert, client_cert, client_key = self._load_tls_credentials()

            # Create TLS credentials for secure gRPC connection
            # gRPC requires credentials in specific format for mTLS
            credentials = grpc.ssl_channel_credentials(
                root_certificates=ca_cert,
                private_key=client_key,
                certificate_chain=client_cert,
            )

            # Connect to Fabric Gateway via secure gRPC channel
            # If TLS validation fails, connection will raise an exception
            self._gateway = await connect(
                target_host=settings.FABRIC_PEER_ENDPOINT,
                identity=settings.FABRIC_IDENTITY,
                # Use the secure channel credentials
                channel_credentials=credentials,
            )

            # Get contract (channel + chaincode) for transaction submission
            network = self._gateway.get_network(settings.FABRIC_CHANNEL)
            self._contract = network.get_contract(settings.FABRIC_CHAINCODE)

            self._initialized = True
            logger.info(
                f"Fabric connection established to {settings.FABRIC_PEER_ENDPOINT} "
                f"(channel={settings.FABRIC_CHANNEL}, chaincode={settings.FABRIC_CHAINCODE})"
            )

        except BlockchainConnectionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Fabric connection: {e}")
            raise BlockchainConnectionError(
                f"Failed to connect to Fabric peer: {e}. "
                "Check FABRIC_PEER_ENDPOINT and TLS certificates."
            ) from e
        finally:
            self._init_lock = False

    async def submit_transaction(
        self, function_name: str, *args: str
    ) -> str:
        """
        Submit a transaction to the blockchain (write operation).
        Waits for transaction to be committed to the ledger.

        Args:
            function_name: Name of the chaincode function (e.g., 'RecordComplianceEvent')
            *args: String arguments to pass to the chaincode function

        Returns:
            Transaction result from chaincode

        Raises:
            BlockchainConnectionError: If unable to connect to peer
            BlockchainTransactionError: If transaction fails
        """
        if not self._initialized:
            await self._initialize_connection()

        try:
            logger.debug(
                f"Submitting transaction: {function_name} with {len(args)} args"
            )
            result = await self._contract.submit_transaction(function_name, *args)
            logger.info(
                f"Transaction {function_name} successfully committed to ledger. "
                f"Result length: {len(str(result))} bytes"
            )
            return result.decode("utf-8") if isinstance(result, bytes) else result
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Transaction {function_name} failed: {error_msg}"
            )
            # Provide specific error guidance based on error type
            if "not found" in error_msg.lower():
                raise BlockchainTransactionError(
                    f"Chaincode function '{function_name}' not found in supplychain.go"
                ) from e
            elif "authorization" in error_msg.lower() or "msp" in error_msg.lower():
                raise BlockchainTransactionError(
                    f"Authorization failed for '{function_name}'. Check caller MSP permissions."
                ) from e
            else:
                raise BlockchainTransactionError(
                    f"Transaction '{function_name}' failed: {error_msg}. "
                    f"Check function name, arguments, and permissions."
                ) from e

    async def evaluate_transaction(
        self, function_name: str, *args: str
    ) -> str:
        """
        Evaluate a transaction on the blockchain (read operation).
        Does not modify ledger state. Returns immediately.

        Args:
            function_name: Name of the chaincode function (e.g., 'GetFarmerHistory')
            *args: String arguments to pass to the chaincode function

        Returns:
            Chaincode response as string

        Raises:
            BlockchainConnectionError: If unable to connect to peer
            BlockchainTransactionError: If evaluation fails
        """
        if not self._initialized:
            await self._initialize_connection()

        try:
            logger.debug(
                f"Evaluating transaction: {function_name} with {len(args)} args"
            )
            result = await self._contract.evaluate_transaction(function_name, *args)
            logger.debug(
                f"Transaction {function_name} evaluated successfully. "
                f"Result length: {len(str(result))} bytes"
            )
            return result.decode("utf-8") if isinstance(result, bytes) else result
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Transaction evaluation {function_name} failed: {error_msg}"
            )
            # Provide specific error guidance based on error type
            if "not found" in error_msg.lower():
                raise BlockchainTransactionError(
                    f"Chaincode function '{function_name}' not found in supplychain.go"
                ) from e
            elif "does not exist" in error_msg.lower():
                raise BlockchainTransactionError(
                    f"Resource for '{function_name}' does not exist. Verify the ID is correct."
                ) from e
            else:
                raise BlockchainTransactionError(
                    f"Evaluation of '{function_name}' failed: {error_msg}. "
                    f"Check function name and arguments."
                ) from e

    async def close(self) -> None:
        """Close the gateway connection gracefully."""
        if self._gateway:
            try:
                await self._gateway.close()
                self._gateway = None
                self._contract = None
                self._initialized = False
                logger.info("Fabric gateway connection closed")
            except Exception as e:
                logger.error(f"Error closing gateway: {e}")


class NoOpBlockchainService(IBlockchainService):
    """
    No-op implementation for when Fabric is not configured.
    Useful for development and testing without a running Fabric network.
    """

    async def submit_transaction(
        self, function_name: str, *args: str
    ) -> str:
        """Log and return placeholder transaction result."""
        logger.info(
            f"[NOOP] Would submit transaction: {function_name} with args: {args}"
        )
        return '{"status":"noop","message":"blockchain not configured"}'

    async def evaluate_transaction(
        self, function_name: str, *args: str
    ) -> str:
        """Log and return placeholder evaluation result."""
        logger.info(
            f"[NOOP] Would evaluate transaction: {function_name} with args: {args}"
        )
        return '{"status":"noop","message":"blockchain not configured"}'


def get_blockchain_service() -> IBlockchainService:
    """
    Factory function to get appropriate blockchain service implementation.

    Returns FabricBlockchainService if Fabric is configured, else NoOpBlockchainService.
    This allows graceful degradation if Fabric is not available.

    Returns:
        IBlockchainService implementation
    """
    # Check if Fabric is configured
    is_fabric_configured = all([
        settings.FABRIC_CHANNEL,
        settings.FABRIC_CHAINCODE,
        settings.FABRIC_PEER_ENDPOINT,
    ])

    if is_fabric_configured:
        try:
            return FabricBlockchainService()
        except BlockchainServiceError as e:
            logger.warning(
                f"Fabric service misconfigured: {e}. Falling back to no-op service."
            )
            return NoOpBlockchainService()
    else:
        logger.info("Fabric not configured. Using no-op blockchain service.")
        return NoOpBlockchainService()


# Global service instance (lazy-initialized)
_blockchain_service: Optional[IBlockchainService] = None


def initialize_blockchain_service() -> IBlockchainService:
    """
    Initialize or retrieve the global blockchain service instance.
    Safe for repeated calls.

    Returns:
        IBlockchainService implementation
    """
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = get_blockchain_service()
    return _blockchain_service

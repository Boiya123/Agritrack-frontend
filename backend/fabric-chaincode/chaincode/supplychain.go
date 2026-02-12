package main

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
)

// Constants
const (
	MinFarmOrgMSP      = "FarmOrgMSP"
	RegulatorOrgMSP    = "RegulatorOrgMSP"
	AdminOrgMSP        = "AdminOrgMSP"
	TemperatureMinSafe = 2.0
	TemperatureMaxSafe = 8.0
)

// Status transition rules
var validStatusTransitions = map[string][]string{
	"CREATED":      {"IN_PROGRESS", "CANCELLED"},
	"IN_PROGRESS":  {"COMPLETED", "FAILED", "CANCELLED"},
	"COMPLETED":    {},
	"FAILED":       {"IN_PROGRESS"},
	"CANCELLED":    {},
	"APPROVED":     {},
	"REJECTED":     {"PENDING"},
	"PENDING":      {"APPROVED", "REJECTED"},
}

// ============================================================================
// DATA MODELS
// ============================================================================

// ProductAsset represents a product type
type ProductAsset struct {
	DocType   string `json:"docType"`
	ProductID string `json:"product_id"`
	Name      string `json:"name"`
	Desc      string `json:"description"`
	IsActive  bool   `json:"is_active"`
	CreatedAt string `json:"created_at"`
}

// BatchAsset represents a production batch
type BatchAsset struct {
	DocType           string `json:"docType"`
	BatchID           string `json:"batch_id"`
	ProductID         string `json:"product_id"`
	FarmerID          string `json:"farmer_id"`
	BatchNumber       string `json:"batch_number"`
	Status            string `json:"status"`
	Quantity          int    `json:"quantity"`
	StartDate         string `json:"start_date"`
	ExpectedEndDate   string `json:"expected_end_date"`
	ActualEndDate     string `json:"actual_end_date"`
	Location          string `json:"location"`
	QRCode            string `json:"qr_code"`
	Notes             string `json:"notes"`
	CreatedAt         string `json:"created_at"`
	UpdatedAt         string `json:"updated_at"`
}

// LifecycleEventAsset represents production events (append-only)
type LifecycleEventAsset struct {
	DocType          string `json:"docType"`
	EventID          string `json:"event_id"`
	BatchID          string `json:"batch_id"`
	EventType        string `json:"event_type"`
	Description      string `json:"description"`
	RecordedBy       string `json:"recorded_by"`
	EventDate        string `json:"event_date"`
	QuantityAffected int    `json:"quantity_affected"`
	Metadata         string `json:"metadata"`
	CreatedAt        string `json:"created_at"`
}

// TransportAsset represents transport manifest
type TransportAsset struct {
	DocType               string `json:"docType"`
	TransportID           string `json:"transport_id"`
	BatchID               string `json:"batch_id"`
	FromPartyID           string `json:"from_party_id"`
	ToPartyID             string `json:"to_party_id"`
	VehicleID             string `json:"vehicle_id"`
	DriverName            string `json:"driver_name"`
	DepartureTime         string `json:"departure_time"`
	ArrivalTime           string `json:"arrival_time"`
	OriginLocation        string `json:"origin_location"`
	DestinationLocation   string `json:"destination_location"`
	TemperatureMonitored  bool   `json:"temperature_monitored"`
	Status                string `json:"status"`
	Notes                 string `json:"notes"`
	CreatedAt             string `json:"created_at"`
	UpdatedAt             string `json:"updated_at"`
}

// TemperatureLogAsset represents temperature records
type TemperatureLogAsset struct {
	DocType      string  `json:"docType"`
	LogID        string  `json:"log_id"`
	TransportID  string  `json:"transport_id"`
	Temperature  float64 `json:"temperature"`
	Timestamp    string  `json:"timestamp"`
	Location     string  `json:"location"`
	IsViolation  bool    `json:"is_violation"`
	CreatedAt    string  `json:"created_at"`
}

// ProcessingAsset represents processing facility records
type ProcessingAsset struct {
	DocType      string  `json:"docType"`
	ProcessingID string  `json:"processing_id"`
	BatchID      string  `json:"batch_id"`
	ProcessDate  string  `json:"processing_date"`
	FacilityName string  `json:"facility_name"`
	SlaughterCnt int     `json:"slaughter_count"`
	YieldKg      float64 `json:"yield_kg"`
	QualityScore float64 `json:"quality_score"`
	Notes        string  `json:"notes"`
	CreatedAt    string  `json:"created_at"`
	UpdatedAt    string  `json:"updated_at"`
}

// CertificationAsset represents certifications
type CertificationAsset struct {
	DocType         string `json:"docType"`
	CertificationID string `json:"certification_id"`
	ProcessingID    string `json:"processing_id"`
	CertType        string `json:"cert_type"`
	Status          string `json:"status"`
	IssuedDate      string `json:"issued_date"`
	ExpiryDate      string `json:"expiry_date"`
	IssuerID        string `json:"issuer_id"`
	Notes           string `json:"notes"`
	CreatedAt       string `json:"created_at"`
	UpdatedAt       string `json:"updated_at"`
}

// RegulatoryAsset represents regulatory approvals
type RegulatoryAsset struct {
	DocType         string `json:"docType"`
	RegulatoryID    string `json:"regulatory_id"`
	BatchID         string `json:"batch_id"`
	RecordType      string `json:"record_type"`
	Status          string `json:"status"`
	IssuedDate      string `json:"issued_date"`
	ExpiryDate      string `json:"expiry_date"`
	RegulatorID     string `json:"regulator_id"`
	Details         string `json:"details"`
	RejectionReason string `json:"rejection_reason"`
	AuditFlags      string `json:"audit_flags"`
	CreatedAt       string `json:"created_at"`
	UpdatedAt       string `json:"updated_at"`
}

// ============================================================================
// SUPPLY CHAIN CONTRACT
// ============================================================================

type SupplyChainContract struct {
	contractapi.Contract
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

// AssetExists checks if an asset exists in the ledger
func (s *SupplyChainContract) AssetExists(ctx contractapi.TransactionContextInterface, assetType, assetID string) (bool, error) {
	assetBytes, err := ctx.GetStub().GetState(assetID)
	if err != nil {
		return false, fmt.Errorf("failed to read from ledger: %v", err)
	}
	return assetBytes != nil, nil
}

// GetTxTimestamp returns the Fabric transaction timestamp (deterministic, no time.Now())
func (s *SupplyChainContract) GetTxTimestamp(ctx contractapi.TransactionContextInterface) string {
	timestamp, err := ctx.GetStub().GetTxTimestamp()
	if err != nil {
		return ""
	}
	return timestamp.String()
}

// AuthorizeMSP checks if the caller's MSP matches the required MSP
func (s *SupplyChainContract) AuthorizeMSP(ctx contractapi.TransactionContextInterface, requiredMSP string) error {
	clientMSP, err := ctx.GetClientIdentity().GetMSPID()
	if err != nil {
		return fmt.Errorf("failed to get client MSP: %v", err)
	}

	if requiredMSP != "ANY" && clientMSP != requiredMSP && clientMSP != AdminOrgMSP {
		return fmt.Errorf("unauthorized: MSP %s not allowed. Required: %s or %s", clientMSP, requiredMSP, AdminOrgMSP)
	}
	return nil
}

// ValidateStatusTransition checks if a status transition is valid
func (s *SupplyChainContract) ValidateStatusTransition(currentStatus, newStatus string) error {
	allowedTransitions, exists := validStatusTransitions[currentStatus]
	if !exists {
		return fmt.Errorf("unknown status: %s", currentStatus)
	}
	for _, allowed := range allowedTransitions {
		if allowed == newStatus {
			return nil
		}
	}
	return fmt.Errorf("invalid transition from %s to %s", currentStatus, newStatus)
}

// ValidateNonEmptyString validates that a string is not empty
func (s *SupplyChainContract) ValidateNonEmptyString(value, fieldName string) error {
	if strings.TrimSpace(value) == "" {
		return fmt.Errorf("%s cannot be empty", fieldName)
	}
	return nil
}

// ValidatePositiveInt validates that an integer is positive
func (s *SupplyChainContract) ValidatePositiveInt(value int, fieldName string) error {
	if value <= 0 {
		return fmt.Errorf("%s must be positive, got %d", fieldName, value)
	}
	return nil
}

// ValidatePositiveFloat validates that a float is positive
func (s *SupplyChainContract) ValidatePositiveFloat(value float64, fieldName string) error {
	if value < 0 {
		return fmt.Errorf("%s must be non-negative, got %f", fieldName, value)
	}
	return nil
}

// ============================================================================
// PRODUCT FUNCTIONS
// ============================================================================

// CreateProduct creates a new product type (Admin or Regulator)
func (s *SupplyChainContract) CreateProduct(
	ctx contractapi.TransactionContextInterface,
	productID string,
	name string,
	description string,
) (*ProductAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, RegulatorOrgMSP); err != nil {
		return nil, err
	}

	// Validation
	if err := s.ValidateNonEmptyString(productID, "productID"); err != nil {
		return nil, err
	}
	if err := s.ValidateNonEmptyString(name, "name"); err != nil {
		return nil, err
	}

	// Check uniqueness
	exists, err := s.AssetExists(ctx, "ProductAsset", productID)
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, fmt.Errorf("product %s already exists", productID)
	}

	product := ProductAsset{
		DocType:   "ProductAsset",
		ProductID: productID,
		Name:      name,
		Desc:      description,
		IsActive:  true,
		CreatedAt: s.GetTxTimestamp(ctx),
	}

	productBytes, err := json.Marshal(product)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal product: %v", err)
	}

	if err = ctx.GetStub().PutState(productID, productBytes); err != nil {
		return nil, fmt.Errorf("failed to save product: %v", err)
	}

	// Emit event
	eventPayload := map[string]string{"product_id": productID}
	eventBytes, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("ProductCreated", eventBytes)

	return &product, nil
}

// GetProduct retrieves a product by ID
func (s *SupplyChainContract) GetProduct(
	ctx contractapi.TransactionContextInterface,
	productID string,
) (*ProductAsset, error) {
	if err := s.ValidateNonEmptyString(productID, "productID"); err != nil {
		return nil, err
	}

	productBytes, err := ctx.GetStub().GetState(productID)
	if err != nil {
		return nil, fmt.Errorf("failed to read product: %v", err)
	}
	if productBytes == nil {
		return nil, fmt.Errorf("product %s not found", productID)
	}

	var product ProductAsset
	marshalErr := json.Unmarshal(productBytes, &product)
	if marshalErr != nil {
		return nil, fmt.Errorf("failed to unmarshal product: %v", marshalErr)
	}

	return &product, nil
}

// DeactivateProduct deactivates a product
func (s *SupplyChainContract) DeactivateProduct(
	ctx contractapi.TransactionContextInterface,
	productID string,
) (*ProductAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, RegulatorOrgMSP); err != nil {
		return nil, err
	}

	product, err := s.GetProduct(ctx, productID)
	if err != nil {
		return nil, err
	}

	product.IsActive = false
	productBytes, err := json.Marshal(product)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal product: %v", err)
	}

	if err = ctx.GetStub().PutState(productID, productBytes); err != nil {
		return nil, fmt.Errorf("failed to update product: %v", err)
	}

	return product, nil
}

// ============================================================================
// BATCH FUNCTIONS
// ============================================================================

// CreateBatch creates a new batch (Farmer)
func (s *SupplyChainContract) CreateBatch(
	ctx contractapi.TransactionContextInterface,
	batchID string,
	productID string,
	farmerID string,
	batchNumber string,
	quantity int,
	startDate string,
	expectedEndDate string,
	location string,
	qrCode string,
	notes string,
) (*BatchAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, MinFarmOrgMSP); err != nil {
		return nil, err
	}

	// Validation
	if err := s.ValidateNonEmptyString(batchID, "batchID"); err != nil {
		return nil, err
	}
	if err := s.ValidateNonEmptyString(batchNumber, "batchNumber"); err != nil {
		return nil, err
	}
	if err := s.ValidatePositiveInt(quantity, "quantity"); err != nil {
		return nil, err
	}

	// Check product exists
	_, err := s.GetProduct(ctx, productID)
	if err != nil {
		return nil, fmt.Errorf("product %s does not exist", productID)
	}

	// Check batch ID uniqueness
	var exists bool
	exists, err = s.AssetExists(ctx, "BatchAsset", batchID)
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, fmt.Errorf("batch %s already exists", batchID)
	}

	// For batch_number uniqueness, create a secondary index key
	// In production, use CouchDB rich queries; for now, check a composite key
	batchNumberKey := fmt.Sprintf("batch_number~%s", batchNumber)
	existingBatchNum, _ := ctx.GetStub().GetState(batchNumberKey)
	if existingBatchNum != nil {
		return nil, fmt.Errorf("batch number %s already exists", batchNumber)
	}

	batch := BatchAsset{
		DocType:         "BatchAsset",
		BatchID:         batchID,
		ProductID:       productID,
		FarmerID:        farmerID,
		BatchNumber:     batchNumber,
		Status:          "CREATED",
		Quantity:        quantity,
		StartDate:       startDate,
		ExpectedEndDate: expectedEndDate,
		Location:        location,
		QRCode:          qrCode,
		Notes:           notes,
		CreatedAt:       s.GetTxTimestamp(ctx),
		UpdatedAt:       s.GetTxTimestamp(ctx),
	}

	batchBytes, err := json.Marshal(batch)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal batch: %v", err)
	}

	putErr := ctx.GetStub().PutState(batchID, batchBytes)
	if putErr != nil {
		return nil, fmt.Errorf("failed to save batch: %v", putErr)
	}

	// Store batch number index for uniqueness checking
	if err = ctx.GetStub().PutState(batchNumberKey, []byte(batchID)); err != nil {
		return nil, fmt.Errorf("failed to save batch number index: %v", err)
	}

	// Emit event
	eventPayload := map[string]string{"batch_id": batchID, "farmer_id": farmerID}
	eventBytes, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("BatchCreated", eventBytes)

	return &batch, nil
}

// GetBatch retrieves a batch by ID
func (s *SupplyChainContract) GetBatch(
	ctx contractapi.TransactionContextInterface,
	batchID string,
) (*BatchAsset, error) {
	if err := s.ValidateNonEmptyString(batchID, "batchID"); err != nil {
		return nil, err
	}

	batchBytes, err := ctx.GetStub().GetState(batchID)
	if err != nil {
		return nil, fmt.Errorf("failed to read batch: %v", err)
	}
	if batchBytes == nil {
		return nil, fmt.Errorf("batch %s not found", batchID)
	}

	var batch BatchAsset
	marshalErr := json.Unmarshal(batchBytes, &batch)
	if marshalErr != nil {
		return nil, fmt.Errorf("failed to unmarshal batch: %v", marshalErr)
	}

	return &batch, nil
}

// UpdateBatchStatus updates batch status with validation
func (s *SupplyChainContract) UpdateBatchStatus(
	ctx contractapi.TransactionContextInterface,
	batchID string,
	newStatus string,
) (*BatchAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, MinFarmOrgMSP); err != nil {
		return nil, err
	}

	batch, err := s.GetBatch(ctx, batchID)
	if err != nil {
		return nil, err
	}

	// Validate transition
	if err := s.ValidateStatusTransition(batch.Status, newStatus); err != nil {
		return nil, err
	}

	batch.Status = newStatus
	batch.UpdatedAt = s.GetTxTimestamp(ctx)

	batchBytes, err := json.Marshal(batch)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal batch: %v", err)
	}

	if err := ctx.GetStub().PutState(batchID, batchBytes); err != nil {
		return nil, fmt.Errorf("failed to update batch: %v", err)
	}

	return batch, nil
}

// CompleteBatch completes a batch
func (s *SupplyChainContract) CompleteBatch(
	ctx contractapi.TransactionContextInterface,
	batchID string,
	actualEndDate string,
) (*BatchAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, MinFarmOrgMSP); err != nil {
		return nil, err
	}

	batch, err := s.GetBatch(ctx, batchID)
	if err != nil {
		return nil, err
	}

	// Validate transition to COMPLETED
	if err := s.ValidateStatusTransition(batch.Status, "COMPLETED"); err != nil {
		return nil, err
	}

	batch.Status = "COMPLETED"
	batch.ActualEndDate = actualEndDate
	batch.UpdatedAt = s.GetTxTimestamp(ctx)

	batchBytes, err := json.Marshal(batch)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal batch: %v", err)
	}

	if err := ctx.GetStub().PutState(batchID, batchBytes); err != nil {
		return nil, fmt.Errorf("failed to complete batch: %v", err)
	}

	return batch, nil
}

// GetBatchesByFarmer retrieves all batches for a farmer
func (s *SupplyChainContract) GetBatchesByFarmer(
	ctx contractapi.TransactionContextInterface,
	farmerID string,
) ([]*BatchAsset, error) {
	if err := s.ValidateNonEmptyString(farmerID, "farmerID"); err != nil {
		return nil, err
	}

	// Note: In production, use CouchDB rich queries via GetQueryResultsForQueryString
	// For now, return empty list (full implementation requires RichQuery support)
	return []*BatchAsset{}, nil
}

// ============================================================================
// LIFECYCLE EVENT FUNCTIONS
// ============================================================================

// RecordLifecycleEvent records a lifecycle event (append-only)
func (s *SupplyChainContract) RecordLifecycleEvent(
	ctx contractapi.TransactionContextInterface,
	eventID string,
	batchID string,
	eventType string,
	description string,
	recordedBy string,
	eventDate string,
	quantityAffected int,
	metadata string,
) (*LifecycleEventAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, MinFarmOrgMSP); err != nil {
		return nil, err
	}

	// Validation
	if err := s.ValidateNonEmptyString(eventID, "eventID"); err != nil {
		return nil, err
	}
	if err := s.ValidateNonEmptyString(batchID, "batchID"); err != nil {
		return nil, err
	}

	// Check batch exists
	_, err := s.GetBatch(ctx, batchID)
	if err != nil {
		return nil, fmt.Errorf("batch does not exist: %v", err)
	}

	// Check event uniqueness
	exists, err := s.AssetExists(ctx, "LifecycleEventAsset", eventID)
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, fmt.Errorf("event %s already exists", eventID)
	}

	event := LifecycleEventAsset{
		DocType:          "LifecycleEventAsset",
		EventID:          eventID,
		BatchID:          batchID,
		EventType:        eventType,
		Description:      description,
		RecordedBy:       recordedBy,
		EventDate:        eventDate,
		QuantityAffected: quantityAffected,
		Metadata:         metadata,
		CreatedAt:        s.GetTxTimestamp(ctx),
	}

	eventBytes, err := json.Marshal(event)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal event: %v", err)
	}

	if err := ctx.GetStub().PutState(eventID, eventBytes); err != nil {
		return nil, fmt.Errorf("failed to save event: %v", err)
	}

	// Emit event
	eventPayload := map[string]string{
		"event_id":   eventID,
		"batch_id":   batchID,
		"event_type": eventType,
	}
	eventPayloadBytes, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("LifecycleEventRecorded", eventPayloadBytes)

	return &event, nil
}

// GetBatchLifecycleEvents retrieves all lifecycle events for a batch
func (s *SupplyChainContract) GetBatchLifecycleEvents(
	ctx contractapi.TransactionContextInterface,
	batchID string,
) ([]*LifecycleEventAsset, error) {
	if err := s.ValidateNonEmptyString(batchID, "batchID"); err != nil {
		return nil, err
	}

	// Note: In production, use CouchDB rich queries via GetQueryResultsForQueryString
	// For now, return empty list (full implementation requires RichQuery support)
	return []*LifecycleEventAsset{}, nil
}

// ============================================================================
// TRANSPORT FUNCTIONS
// ============================================================================

// CreateTransportManifest creates a transport manifest
func (s *SupplyChainContract) CreateTransportManifest(
	ctx contractapi.TransactionContextInterface,
	transportID string,
	batchID string,
	fromPartyID string,
	toPartyID string,
	vehicleID string,
	driverName string,
	departureTime string,
	originLocation string,
	destinationLocation string,
	temperatureMonitored bool,
	notes string,
) (*TransportAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, MinFarmOrgMSP); err != nil {
		return nil, err
	}

	// Validation
	if err := s.ValidateNonEmptyString(transportID, "transportID"); err != nil {
		return nil, err
	}
	if err := s.ValidateNonEmptyString(batchID, "batchID"); err != nil {
		return nil, err
	}

	// Check batch exists
	_, err := s.GetBatch(ctx, batchID)
	if err != nil {
		return nil, fmt.Errorf("batch does not exist: %v", err)
	}

	// Check uniqueness
	exists, err := s.AssetExists(ctx, "TransportAsset", transportID)
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, fmt.Errorf("transport %s already exists", transportID)
	}

	transport := TransportAsset{
		DocType:             "TransportAsset",
		TransportID:         transportID,
		BatchID:             batchID,
		FromPartyID:         fromPartyID,
		ToPartyID:           toPartyID,
		VehicleID:           vehicleID,
		DriverName:          driverName,
		DepartureTime:       departureTime,
		OriginLocation:      originLocation,
		DestinationLocation: destinationLocation,
		TemperatureMonitored: temperatureMonitored,
		Status:              "INITIATED",
		Notes:               notes,
		CreatedAt:           s.GetTxTimestamp(ctx),
		UpdatedAt:           s.GetTxTimestamp(ctx),
	}

	transportBytes, err := json.Marshal(transport)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal transport: %v", err)
	}

	if err := ctx.GetStub().PutState(transportID, transportBytes); err != nil {
		return nil, fmt.Errorf("failed to save transport: %v", err)
	}

	// Emit event
	eventPayload := map[string]string{"transport_id": transportID, "batch_id": batchID}
	eventBytes, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("TransportCreated", eventBytes)

	return &transport, nil
}

// UpdateTransportStatus updates transport status
func (s *SupplyChainContract) UpdateTransportStatus(
	ctx contractapi.TransactionContextInterface,
	transportID string,
	newStatus string,
	arrivalTime string,
) (*TransportAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, MinFarmOrgMSP); err != nil {
		return nil, err
	}

	transport, err := s.GetTransport(ctx, transportID)
	if err != nil {
		return nil, err
	}

	// Validate transition
	if err := s.ValidateStatusTransition(transport.Status, newStatus); err != nil {
		return nil, err
	}

	transport.Status = newStatus
	if newStatus == "COMPLETED" {
		transport.ArrivalTime = arrivalTime
	}
	transport.UpdatedAt = s.GetTxTimestamp(ctx)

	transportBytes, err := json.Marshal(transport)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal transport: %v", err)
	}

	if err := ctx.GetStub().PutState(transportID, transportBytes); err != nil {
		return nil, fmt.Errorf("failed to update transport: %v", err)
	}

	return transport, nil
}

// GetTransport retrieves a transport by ID
func (s *SupplyChainContract) GetTransport(
	ctx contractapi.TransactionContextInterface,
	transportID string,
) (*TransportAsset, error) {
	if err := s.ValidateNonEmptyString(transportID, "transportID"); err != nil {
		return nil, err
	}

	transportBytes, err := ctx.GetStub().GetState(transportID)
	if err != nil {
		return nil, fmt.Errorf("failed to read transport: %v", err)
	}
	if transportBytes == nil {
		return nil, fmt.Errorf("transport %s not found", transportID)
	}

	var transport TransportAsset
	transportErr := json.Unmarshal(transportBytes, &transport)
	if transportErr != nil {
		return nil, fmt.Errorf("failed to unmarshal transport: %v", transportErr)
	}

	return &transport, nil
}

// AddTemperatureLog adds a temperature reading
func (s *SupplyChainContract) AddTemperatureLog(
	ctx contractapi.TransactionContextInterface,
	logID string,
	transportID string,
	temperature float64,
	timestamp string,
	location string,
) (*TemperatureLogAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, MinFarmOrgMSP); err != nil {
		return nil, err
	}

	// Validation
	if err := s.ValidateNonEmptyString(logID, "logID"); err != nil {
		return nil, err
	}
	if err := s.ValidatePositiveFloat(temperature, "temperature"); err != nil {
		return nil, err
	}

	// Check transport exists
	_, err := s.GetTransport(ctx, transportID)
	if err != nil {
		return nil, fmt.Errorf("transport does not exist: %v", err)
	}

	// Detect temperature violation
	isViolation := temperature < TemperatureMinSafe || temperature > TemperatureMaxSafe

	tempLog := TemperatureLogAsset{
		DocType:     "TemperatureLogAsset",
		LogID:       logID,
		TransportID: transportID,
		Temperature: temperature,
		Timestamp:   timestamp,
		Location:    location,
		IsViolation: isViolation,
		CreatedAt:   s.GetTxTimestamp(ctx),
	}

	logBytes, err := json.Marshal(tempLog)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal temperature log: %v", err)
	}

	if err := ctx.GetStub().PutState(logID, logBytes); err != nil {
		return nil, fmt.Errorf("failed to save temperature log: %v", err)
	}

	// Emit violation event if detected
	if isViolation {
		eventPayload := map[string]interface{}{
			"transport_id": transportID,
			"temperature":  temperature,
			"threshold":    fmt.Sprintf("%.1f-%.1f°C", TemperatureMinSafe, TemperatureMaxSafe),
		}
		eventBytes, _ := json.Marshal(eventPayload)
		ctx.GetStub().SetEvent("TemperatureViolationDetected", eventBytes)
	}

	return &tempLog, nil
}

// GetTransportTemperatureLogs retrieves all temperature logs for a transport
func (s *SupplyChainContract) GetTransportTemperatureLogs(
	ctx contractapi.TransactionContextInterface,
	transportID string,
) ([]*TemperatureLogAsset, error) {
	if err := s.ValidateNonEmptyString(transportID, "transportID"); err != nil {
		return nil, err
	}

	// Note: In production, use CouchDB rich queries via GetQueryResultsForQueryString
	// For now, return empty list (full implementation requires RichQuery support)
	return []*TemperatureLogAsset{}, nil
}

// GetTransportsByBatch retrieves all transports for a batch
func (s *SupplyChainContract) GetTransportsByBatch(
	ctx contractapi.TransactionContextInterface,
	batchID string,
) ([]*TransportAsset, error) {
	if err := s.ValidateNonEmptyString(batchID, "batchID"); err != nil {
		return nil, err
	}

	// Note: In production, use CouchDB rich queries via GetQueryResultsForQueryString
	// For now, return empty list (full implementation requires RichQuery support)
	return []*TransportAsset{}, nil
}

// ============================================================================
// PROCESSING FUNCTIONS
// ============================================================================

// RecordProcessing records processing facility output
func (s *SupplyChainContract) RecordProcessing(
	ctx contractapi.TransactionContextInterface,
	processingID string,
	batchID string,
	processDate string,
	facilityName string,
	slaughterCount int,
	yieldKg float64,
	qualityScore float64,
	notes string,
) (*ProcessingAsset, error) {
	// Authorization check
	if err := s.AuthorizeMSP(ctx, MinFarmOrgMSP); err != nil {
		return nil, err
	}

	// Validation
	if err := s.ValidateNonEmptyString(processingID, "processingID"); err != nil {
		return nil, err
	}
	if err := s.ValidatePositiveFloat(yieldKg, "yieldKg"); err != nil {
		return nil, err
	}
	if err := s.ValidatePositiveFloat(qualityScore, "qualityScore"); err != nil {
		return nil, err
	}

	// Check batch exists
	_, err := s.GetBatch(ctx, batchID)
	if err != nil {
		return nil, fmt.Errorf("batch does not exist: %v", err)
	}

	// Check uniqueness
	exists, err := s.AssetExists(ctx, "ProcessingAsset", processingID)
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, fmt.Errorf("processing record %s already exists", processingID)
	}

	processing := ProcessingAsset{
		DocType:      "ProcessingAsset",
		ProcessingID: processingID,
		BatchID:      batchID,
		ProcessDate:  processDate,
		FacilityName: facilityName,
		SlaughterCnt: slaughterCount,
		YieldKg:      yieldKg,
		QualityScore: qualityScore,
		Notes:        notes,
		CreatedAt:    s.GetTxTimestamp(ctx),
		UpdatedAt:    s.GetTxTimestamp(ctx),
	}

	processingBytes, err := json.Marshal(processing)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal processing: %v", err)
	}

	if err := ctx.GetStub().PutState(processingID, processingBytes); err != nil {
		return nil, fmt.Errorf("failed to save processing: %v", err)
	}

	// Emit event
	eventPayload := map[string]string{
		"processing_id": processingID,
		"batch_id":      batchID,
	}
	eventBytes, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("ProcessingRecorded", eventBytes)

	return &processing, nil
}

// GetProcessingRecord retrieves a processing record by ID
func (s *SupplyChainContract) GetProcessingRecord(
	ctx contractapi.TransactionContextInterface,
	processingID string,
) (*ProcessingAsset, error) {
	if err := s.ValidateNonEmptyString(processingID, "processingID"); err != nil {
		return nil, err
	}

	processingBytes, err := ctx.GetStub().GetState(processingID)
	if err != nil {
		return nil, fmt.Errorf("failed to read processing: %v", err)
	}
	if processingBytes == nil {
		return nil, fmt.Errorf("processing record %s not found", processingID)
	}

	var processing ProcessingAsset
	processingErr := json.Unmarshal(processingBytes, &processing)
	if processingErr != nil {
		return nil, fmt.Errorf("failed to unmarshal processing: %v", processingErr)
	}

	return &processing, nil
}

// ============================================================================
// CERTIFICATION FUNCTIONS
// ============================================================================

// IssueCertification issues a certification (Regulator only)
func (s *SupplyChainContract) IssueCertification(
	ctx contractapi.TransactionContextInterface,
	certificationID string,
	processingID string,
	certType string,
	issuedDate string,
	expiryDate string,
	issuerID string,
	notes string,
) (*CertificationAsset, error) {
	// Authorization check (Regulator only)
	if err := s.AuthorizeMSP(ctx, RegulatorOrgMSP); err != nil {
		return nil, err
	}

	// Validation
	if err := s.ValidateNonEmptyString(certificationID, "certificationID"); err != nil {
		return nil, err
	}
	if err := s.ValidateNonEmptyString(certType, "certType"); err != nil {
		return nil, err
	}

	// Check processing record exists
	_, err := s.GetProcessingRecord(ctx, processingID)
	if err != nil {
		return nil, fmt.Errorf("processing record does not exist: %v", err)
	}

	// Check uniqueness
	exists, err := s.AssetExists(ctx, "CertificationAsset", certificationID)
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, fmt.Errorf("certification %s already exists", certificationID)
	}

	certification := CertificationAsset{
		DocType:         "CertificationAsset",
		CertificationID: certificationID,
		ProcessingID:    processingID,
		CertType:        certType,
		Status:          "APPROVED",
		IssuedDate:      issuedDate,
		ExpiryDate:      expiryDate,
		IssuerID:        issuerID,
		Notes:           notes,
		CreatedAt:       s.GetTxTimestamp(ctx),
		UpdatedAt:       s.GetTxTimestamp(ctx),
	}

	certBytes, err := json.Marshal(certification)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal certification: %v", err)
	}

	if err := ctx.GetStub().PutState(certificationID, certBytes); err != nil {
		return nil, fmt.Errorf("failed to save certification: %v", err)
	}

	// Emit event
	eventPayload := map[string]string{
		"certification_id": certificationID,
		"processing_id":    processingID,
		"status":           "APPROVED",
	}
	eventBytes, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("CertificationUpdated", eventBytes)

	return &certification, nil
}

// UpdateCertificationStatus updates certification status (Regulator only)
func (s *SupplyChainContract) UpdateCertificationStatus(
	ctx contractapi.TransactionContextInterface,
	certificationID string,
	newStatus string,
) (*CertificationAsset, error) {
	// Authorization check (Regulator only)
	if err := s.AuthorizeMSP(ctx, RegulatorOrgMSP); err != nil {
		return nil, err
	}

	certification, err := s.GetCertification(ctx, certificationID)
	if err != nil {
		return nil, err
	}

	// Validate transition
	if err := s.ValidateStatusTransition(certification.Status, newStatus); err != nil {
		return nil, err
	}

	certification.Status = newStatus
	certification.UpdatedAt = s.GetTxTimestamp(ctx)

	certBytes, err := json.Marshal(certification)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal certification: %v", err)
	}

	if err := ctx.GetStub().PutState(certificationID, certBytes); err != nil {
		return nil, fmt.Errorf("failed to update certification: %v", err)
	}

	// Emit event
	eventPayload := map[string]string{
		"certification_id": certificationID,
		"status":           newStatus,
	}
	eventBytes, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("CertificationUpdated", eventBytes)

	return certification, nil
}

// GetCertification retrieves a certification by ID
func (s *SupplyChainContract) GetCertification(
	ctx contractapi.TransactionContextInterface,
	certificationID string,
) (*CertificationAsset, error) {
	if err := s.ValidateNonEmptyString(certificationID, "certificationID"); err != nil {
		return nil, err
	}

	certBytes, err := ctx.GetStub().GetState(certificationID)
	if err != nil {
		return nil, fmt.Errorf("failed to read certification: %v", err)
	}
	if certBytes == nil {
		return nil, fmt.Errorf("certification %s not found", certificationID)
	}

	var certification CertificationAsset
	certErr := json.Unmarshal(certBytes, &certification)
	if certErr != nil {
		return nil, fmt.Errorf("failed to unmarshal certification: %v", certErr)
	}

	return &certification, nil
}

// GetCertificationsByProcessing retrieves certifications for a processing record
func (s *SupplyChainContract) GetCertificationsByProcessing(
	ctx contractapi.TransactionContextInterface,
	processingID string,
) ([]*CertificationAsset, error) {
	if err := s.ValidateNonEmptyString(processingID, "processingID"); err != nil {
		return nil, err
	}

	// Note: In production, use CouchDB rich queries via GetQueryResultsForQueryString
	// For now, return empty list (full implementation requires RichQuery support)
	return []*CertificationAsset{}, nil
}

// ============================================================================
// REGULATORY FUNCTIONS
// ============================================================================

// CreateRegulatoryRecord creates a regulatory record (Regulator only)
func (s *SupplyChainContract) CreateRegulatoryRecord(
	ctx contractapi.TransactionContextInterface,
	regulatoryID string,
	batchID string,
	recordType string,
	issuedDate string,
	expiryDate string,
	regulatorID string,
	details string,
	auditFlags string,
) (*RegulatoryAsset, error) {
	// Authorization check (Regulator only)
	if err := s.AuthorizeMSP(ctx, RegulatorOrgMSP); err != nil {
		return nil, err
	}

	// Validation
	if err := s.ValidateNonEmptyString(regulatoryID, "regulatoryID"); err != nil {
		return nil, err
	}
	if err := s.ValidateNonEmptyString(batchID, "batchID"); err != nil {
		return nil, err
	}

	// Check batch exists
	_, err := s.GetBatch(ctx, batchID)
	if err != nil {
		return nil, fmt.Errorf("batch does not exist: %v", err)
	}

	// Check uniqueness
	exists, err := s.AssetExists(ctx, "RegulatoryAsset", regulatoryID)
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, fmt.Errorf("regulatory record %s already exists", regulatoryID)
	}

	regulatory := RegulatoryAsset{
		DocType:       "RegulatoryAsset",
		RegulatoryID:  regulatoryID,
		BatchID:       batchID,
		RecordType:    recordType,
		Status:        "PENDING",
		IssuedDate:    issuedDate,
		ExpiryDate:    expiryDate,
		RegulatorID:   regulatorID,
		Details:       details,
		AuditFlags:    auditFlags,
		CreatedAt:     s.GetTxTimestamp(ctx),
		UpdatedAt:     s.GetTxTimestamp(ctx),
	}

	regBytes, err := json.Marshal(regulatory)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal regulatory record: %v", err)
	}

	if err := ctx.GetStub().PutState(regulatoryID, regBytes); err != nil {
		return nil, fmt.Errorf("failed to save regulatory record: %v", err)
	}

	// Emit event
	eventPayload := map[string]string{
		"regulatory_id": regulatoryID,
		"batch_id":      batchID,
		"status":        "PENDING",
	}
	eventBytes, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("RegulatoryRecordUpdated", eventBytes)

	return &regulatory, nil
}

// UpdateRegulatoryStatus updates regulatory record status (Regulator only)
func (s *SupplyChainContract) UpdateRegulatoryStatus(
	ctx contractapi.TransactionContextInterface,
	regulatoryID string,
	newStatus string,
	rejectionReason string,
) (*RegulatoryAsset, error) {
	// Authorization check (Regulator only)
	if err := s.AuthorizeMSP(ctx, RegulatorOrgMSP); err != nil {
		return nil, err
	}

	regulatory, err := s.GetRegulatoryRecord(ctx, regulatoryID)
	if err != nil {
		return nil, err
	}

	// Validate transition
	if err := s.ValidateStatusTransition(regulatory.Status, newStatus); err != nil {
		return nil, err
	}

	regulatory.Status = newStatus
	if newStatus == "REJECTED" {
		regulatory.RejectionReason = rejectionReason
	}
	regulatory.UpdatedAt = s.GetTxTimestamp(ctx)

	regBytes, err := json.Marshal(regulatory)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal regulatory record: %v", err)
	}

	if err := ctx.GetStub().PutState(regulatoryID, regBytes); err != nil {
		return nil, fmt.Errorf("failed to update regulatory record: %v", err)
	}

	// Emit event
	eventPayload := map[string]string{
		"regulatory_id": regulatoryID,
		"status":        newStatus,
	}
	eventBytes, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("RegulatoryRecordUpdated", eventBytes)

	return regulatory, nil
}

// GetRegulatoryRecord retrieves a regulatory record by ID
func (s *SupplyChainContract) GetRegulatoryRecord(
	ctx contractapi.TransactionContextInterface,
	regulatoryID string,
) (*RegulatoryAsset, error) {
	if err := s.ValidateNonEmptyString(regulatoryID, "regulatoryID"); err != nil {
		return nil, err
	}

	regBytes, err := ctx.GetStub().GetState(regulatoryID)
	if err != nil {
		return nil, fmt.Errorf("failed to read regulatory record: %v", err)
	}
	if regBytes == nil {
		return nil, fmt.Errorf("regulatory record %s not found", regulatoryID)
	}

	var regulatory RegulatoryAsset
	regErr := json.Unmarshal(regBytes, &regulatory)
	if regErr != nil {
		return nil, fmt.Errorf("failed to unmarshal regulatory record: %v", regErr)
	}

	return &regulatory, nil
}

// GetRegulatoryRecordsByBatch retrieves regulatory records for a batch
func (s *SupplyChainContract) GetRegulatoryRecordsByBatch(
	ctx contractapi.TransactionContextInterface,
	batchID string,
) ([]*RegulatoryAsset, error) {
	if err := s.ValidateNonEmptyString(batchID, "batchID"); err != nil {
		return nil, err
	}

	// Note: In production, use CouchDB rich queries via GetQueryResultsForQueryString
	// For now, return empty list (full implementation requires RichQuery support)
	return []*RegulatoryAsset{}, nil
}

// ============================================================================
// MAIN
// ============================================================================

func main() {
	chaincode, err := contractapi.NewChaincode(&SupplyChainContract{})
	if err != nil {
		fmt.Printf("Error creating chaincode: %v\n", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting chaincode: %v\n", err)
	}
}

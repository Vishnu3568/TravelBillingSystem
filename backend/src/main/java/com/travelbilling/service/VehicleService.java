package com.travelbilling.service;

import com.travelbilling.dto.VehicleRequest;
import com.travelbilling.dto.VehicleResponse;
import com.travelbilling.entity.Vehicle;
import com.travelbilling.repository.VehicleRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class VehicleService {

    private final VehicleRepository vehicleRepository;
    private final AuditLogService auditLogService;

    public List<VehicleResponse> getAllVehicles() {
        return vehicleRepository.findAll().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    @Transactional
    public VehicleResponse createVehicle(VehicleRequest request) {
        Vehicle vehicle = Vehicle.builder()
                .registrationNumber(request.getRegistrationNumber())
                .type(request.getType())
                .model(request.getModel())
                .build();
        Vehicle saved = vehicleRepository.save(vehicle);
        auditLogService.logAction("CREATE_VEHICLE", "VEHICLE", "Created vehicle: " + saved.getRegistrationNumber());
        return mapToResponse(saved);
    }

    @Transactional
    public VehicleResponse updateVehicle(Long id, VehicleRequest request) {
        Vehicle vehicle = vehicleRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Vehicle not found"));
        
        vehicle.setRegistrationNumber(request.getRegistrationNumber());
        vehicle.setType(request.getType());
        vehicle.setModel(request.getModel());
        
        Vehicle saved = vehicleRepository.save(vehicle);
        auditLogService.logAction("UPDATE_VEHICLE", "VEHICLE", "Updated vehicle: " + saved.getRegistrationNumber());
        return mapToResponse(saved);
    }

    @Transactional
    public void deleteVehicle(Long id) {
        Vehicle vehicle = vehicleRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Vehicle not found"));
        String reg = vehicle.getRegistrationNumber();
        vehicleRepository.delete(vehicle);
        auditLogService.logAction("DELETE_VEHICLE", "VEHICLE", "Deleted vehicle: " + reg);
    }

    private VehicleResponse mapToResponse(Vehicle vehicle) {
        return VehicleResponse.builder()
                .id(vehicle.getId())
                .registrationNumber(vehicle.getRegistrationNumber())
                .type(vehicle.getType())
                .model(vehicle.getModel())
                .createdAt(vehicle.getCreatedAt())
                .updatedAt(vehicle.getUpdatedAt())
                .build();
    }
}

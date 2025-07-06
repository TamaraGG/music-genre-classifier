package com.example.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.Map;

@Data
@AllArgsConstructor
public class PredictionResultDTO {
    private String identifiedGenre;
    private Map<String, Double> allProbabilities;
}

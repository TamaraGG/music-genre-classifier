package com.example.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.Map;

@Data
public class AIResponseDTO {
    @JsonProperty("top_genre")
    private String topGenre;

    @JsonProperty("genre_probabilities")
    private Map<String, Double> genreProbabilities;
}

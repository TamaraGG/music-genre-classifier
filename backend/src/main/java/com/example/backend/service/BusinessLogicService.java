package com.example.backend.service;

import com.example.backend.dto.AIResponseDTO;
import com.example.backend.dto.PredictionResultDTO;
import com.example.backend.entity.PredictionHistory;
import com.example.backend.repository.PredictionHistoryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.http.codec.multipart.FilePart;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class BusinessLogicService {

    private final AIServiceClient aiServiceClient;
    private final PredictionHistoryRepository historyRepository;

    public Mono<PredictionResultDTO> classifyAudio(FilePart filePart) {
        return aiServiceClient.getPrediction(filePart)
                .flatMap(aiResponse -> {
                    saveHistory(filePart.filename(), aiResponse);

                    PredictionResultDTO result = new PredictionResultDTO(
                            aiResponse.getTopGenre(),
                            aiResponse.getGenreProbabilities()
                    );
                    return Mono.just(result);
                });
    }

    public List<PredictionHistory> getHistory() {
        return historyRepository.findAll(Sort.by(Sort.Direction.DESC, "predictionTimestamp"));
    }

    private void saveHistory(String fileName, AIResponseDTO response) {
        PredictionHistory history = new PredictionHistory();
        history.setFileName(fileName);
        history.setPredictedGenre(response.getTopGenre());
        history.setPredictionTimestamp(LocalDateTime.now());
        historyRepository.save(history);
    }
}
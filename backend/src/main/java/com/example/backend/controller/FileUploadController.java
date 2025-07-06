package com.example.backend.controller;

import com.example.backend.dto.PredictionResultDTO;
import com.example.backend.service.BusinessLogicService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.codec.multipart.FilePart;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;
import com.example.backend.entity.PredictionHistory;
import org.springframework.web.bind.annotation.GetMapping;
import java.util.List;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class FileUploadController {

    private final BusinessLogicService businessLogicService;

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Mono<ResponseEntity<PredictionResultDTO>> uploadFile(@RequestPart("file") FilePart filePart) {

        return businessLogicService.classifyAudio(filePart)
                .map(ResponseEntity::ok)
                .defaultIfEmpty(ResponseEntity.status(500).build());
    }

    @GetMapping("/history")
    public Mono<ResponseEntity<List<PredictionHistory>>> getHistory() {
        return Mono.just(ResponseEntity.ok(businessLogicService.getHistory()));
    }

}
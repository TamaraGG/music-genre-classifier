package com.example.backend.repository;

import com.example.backend.entity.PredictionHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PredictionHistoryRepository extends JpaRepository<PredictionHistory, Long> {
}

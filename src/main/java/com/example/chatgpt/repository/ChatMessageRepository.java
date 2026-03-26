package com.example.chatgpt.repository;

import com.example.chatgpt.model.ChatMessage;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface ChatMessageRepository extends MongoRepository<ChatMessage, String> {
    List<ChatMessage> findBySessionIdOrderByCreatedAtAsc(String sessionId);
}

package com.example.chatgpt.controller;

import com.example.chatgpt.dto.SendMessageResponse;
import com.example.chatgpt.service.ChatService;
import jakarta.validation.constraints.NotBlank;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/chat")
@Validated
public class ChatController {
    private final ChatService chatService;

    @PostMapping(path = "/{sessionId}/send", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public SendMessageResponse sendMessage(
            @PathVariable String sessionId,
            @RequestPart("content") @NotBlank String content,
            @RequestPart(value = "file", required = false) MultipartFile file) {
        return chatService.sendMessage(sessionId, content, file);
    }
}

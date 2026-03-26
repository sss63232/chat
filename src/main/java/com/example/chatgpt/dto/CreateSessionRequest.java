package com.example.chatgpt.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CreateSessionRequest {
    @NotBlank
    private String userId;

    @NotBlank
    private String title;
}

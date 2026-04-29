package com.project.backend_core.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class TestConnectionController {

    @GetMapping
    public String testConnection(){
        return "Connection Successful";
    }
}

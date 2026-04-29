package com.project.backend_core.dto;

import com.project.backend_core.entity.Facility;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class CameraCreateDto {
    private Facility facility;
    private String name;
    private String rtspUrl;
    private Boolean isActive;
}

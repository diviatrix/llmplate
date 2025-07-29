"""Generation API endpoints."""
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.generation.service import generation_service


router = APIRouter(prefix="/api/v1", tags=["generation"])


class GenerationRequest(BaseModel):
    """Request model for starting generation."""
    
    template_id: str = Field(..., description="Template ID to use")
    provider: str = Field(..., description="LLM provider (openrouter/ollama)")
    model: str = Field(..., description="Model identifier")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    count: int = Field(1, ge=1, le=100, description="Number of items to generate")


class BatchGenerationRequest(BaseModel):
    """Request model for batch generation."""
    
    generations: List[GenerationRequest] = Field(..., min_items=1, max_items=10)


class GenerationResponse(BaseModel):
    """Response model for generation status."""
    
    job_id: str
    status: str
    template_id: str
    provider: str
    model: str
    progress: int = 0
    created_at: str


class ExportFormat(str):
    """Supported export formats."""
    
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    XLSX = "xlsx"
    MARKDOWN = "markdown"
    HTML = "html"
    XML = "xml"
    TXT = "txt"


@router.post("/generate", response_model=GenerationResponse, status_code=202)
async def start_generation(
    request: GenerationRequest,
    current_user: User = Depends(get_current_user)
) -> GenerationResponse:
    """Start a new generation job."""
    try:
        generation = await generation_service.start_generation(
            user=current_user,
            template_id=request.template_id,
            provider=request.provider,
            model=request.model,
            variables=request.variables,
            count=request.count
        )
        
        return GenerationResponse(
            job_id=generation.job_id,
            status=generation.status.value,
            template_id=generation.template_id,
            provider=generation.provider,
            model=generation.model,
            progress=generation.progress,
            created_at=generation.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Template not found")
        raise HTTPException(status_code=500, detail="Failed to start generation")


@router.get("/generate/{job_id}")
async def get_generation_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get generation job status."""
    generation = await generation_service.get_generation_status(job_id, current_user)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation job not found")
    
    return generation.dict_public()


@router.get("/generate/{job_id}/result")
async def get_generation_result(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get generation results if completed."""
    try:
        generation = await generation_service.get_generation_result(job_id, current_user)
        if not generation:
            raise HTTPException(status_code=404, detail="Generation job not found")
        
        return generation.dict_public()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/generate/{job_id}")
async def cancel_generation(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Cancel a generation job."""
    try:
        await generation_service.cancel_generation(job_id, current_user)
        return {"message": "Generation cancelled"}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_generation_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    template_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user's generation history."""
    return await generation_service.get_user_history(
        user=current_user,
        skip=skip,
        limit=limit,
        status=status,
        template_id=template_id
    )


@router.get("/generate/{job_id}/export")
async def export_generation(
    job_id: str,
    format: ExportFormat = Query(ExportFormat.JSON),
    current_user: User = Depends(get_current_user)
):
    """Export generation results in specified format."""
    from fastapi.responses import Response, JSONResponse
    
    try:
        export_data = await generation_service.export_generation(
            job_id, current_user, format.value
        )
        
        # Return appropriate response based on format
        if format == ExportFormat.JSON:
            return JSONResponse(content=export_data)
        
        elif format == ExportFormat.CSV:
            return Response(
                content=export_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=generation_{job_id}.csv"
                }
            )
        
        elif format == ExportFormat.MARKDOWN:
            return Response(
                content=export_data,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename=generation_{job_id}.md"
                }
            )
        
        elif format == ExportFormat.HTML:
            return Response(
                content=export_data,
                media_type="text/html",
                headers={
                    "Content-Disposition": f"inline; filename=generation_{job_id}.html"
                }
            )
        
        elif format == ExportFormat.XML:
            return Response(
                content=export_data,
                media_type="application/xml",
                headers={
                    "Content-Disposition": f"attachment; filename=generation_{job_id}.xml"
                }
            )
        
        elif format == ExportFormat.TXT:
            return Response(
                content=export_data,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename=generation_{job_id}.txt"
                }
            )
        
        elif format == ExportFormat.XLSX:
            # For Excel, we need to create actual file
            import io
            import pandas as pd
            
            excel_data = export_data["sheets"][0]["data"]
            df = pd.DataFrame(excel_data)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Results', index=False)
            
            return Response(
                content=output.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=generation_{job_id}.xlsx"
                }
            )
        
        elif format == ExportFormat.PDF:
            # For PDF, we'll use reportlab
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            import io
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            elements.append(Paragraph(export_data["title"], styles['Title']))
            elements.append(Paragraph(f"Generated: {export_data['generated_at']}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Results
            for i, result in enumerate(export_data["results"], 1):
                elements.append(Paragraph(f"Result {i}", styles['Heading2']))
                
                # Convert result to table data
                table_data = []
                for key, value in result.items():
                    table_data.append([str(key), str(value)])
                
                if table_data:
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(t)
                    elements.append(Spacer(1, 20))
            
            doc.build(elements)
            
            return Response(
                content=buffer.getvalue(),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=generation_{job_id}.pdf"
                }
            )
        
        else:
            return JSONResponse(content=export_data)
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/generate/batch", status_code=202)
async def start_batch_generation(
    request: BatchGenerationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[Dict[str, Any]]]:
    """Start multiple generation jobs."""
    jobs = await generation_service.start_batch_generation(
        user=current_user,
        generations=[gen.dict() for gen in request.generations]
    )
    return {"jobs": jobs}
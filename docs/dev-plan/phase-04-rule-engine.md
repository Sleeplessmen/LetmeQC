# Phase 4: Custom Rule Engine & Guideline Integration

## 📌 Overview

**Duration:** 3 weeks  
**Start Date:** 2026-01-07  
**End Date:** 2026-01-28  
**Status:** ⏳ Planned  
**Priority:** 🟡 MEDIUM

---

## 🎯 Objectives

Implement **custom rule engine** that:
- Parses guidelines (text, JSON, XML, Markdown)
- Supports custom rule sets
- Allows dynamic rule configuration
- Integrates with QC service

---

## 🏗️ Rule Engine Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        RULE ENGINE                            │
├─────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │
│  │  Guideline   │    │  Rule Set   │    │   Rule          │   │
│  │  Parser      │───▶│  Manager    │───▶│   Evaluator     │   │
│  └─────────────┘    └─────────────┘    └─────────────────┘   │
│         │                   │                     │            │
│         ▼                   ▼                     ▼            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │
│  │ Text/JSON    │    │ Multiple    │    │ Validate        │   │
│  │ XML/MD       │    │ Rule Sets   │    │ Annotations     │   │
│  └─────────────┘    └─────────────┘    └─────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Detailed Tasks

### 4.1 Guideline Parser

**Duration:** Week 1 (Day 1-3)  
**Owner:** Backend Dev  
**Estimate:** 3 days

#### Tasks
| ID | Task | Description | Estimate |
|----|------|-------------|----------|
| GP-01 | Support text-based guidelines | Parse plain text guidelines | 1 day |
| GP-02 | Support JSON guidelines | Parse JSON configuration | 1 day |
| GP-03 | Support XML guidelines | Parse XML configuration | 0.5 day |
| GP-04 | Support Markdown guidelines | Parse markdown guidelines | 0.5 day |
| GP-05 | Extract rules from guidelines | Convert guidelines to rules | 2 days |

#### Guideline Format Examples

**Text Format:**
```
# Bounding Box Guidelines

## Minimum Size
- Bounding boxes must have minimum area of 100 pixels
- Minimum width and height: 10 pixels

## Overlap
- Maximum IOU between boxes: 0.95
- Duplicate threshold (IOU): 0.98

## Aspect Ratio
- Maximum aspect ratio: 10.0
- Minimum aspect ratio: 0.1
```

**JSON Format:**
```json
{
  "name": "Standard QC Rules",
  "version": "1.0",
  "rules": [
    {
      "type": "bbox_min_area",
      "params": {"min_area": 100},
      "severity": "high",
      "message": "Bounding box area too small (min: 100)"
    },
    {
      "type": "bbox_iou",
      "params": {"max_iou": 0.95, "duplicate_threshold": 0.98},
      "severity": "critical",
      "message": "Bounding boxes overlap too much"
    }
  ]
}
```

#### Parser Implementation

```python
# src/rules/parsers/guideline_parser.py
import json
import xml.etree.ElementTree as ET
import re
from typing import Dict, Any, List, Union
from pathlib import Path

from src.models.rule import Rule, RuleSet, RuleType, Severity


class GuidelineParser:
    """Parse various guideline formats into Rule objects."""
    
    @staticmethod
    def parse_text(text: str) -> List[Rule]:
        """Parse text-based guidelines."""
        rules = []
        
        # Pattern for bbox min area
        min_area_match = re.search(r'minimum area of (\d+) pixels', text)
        if min_area_match:
            min_area = int(min_area_match.group(1))
            rules.append(Rule(
                name="bbox_min_area",
                rule_type=RuleType.BBOX_MIN_AREA,
                params={"min_area": min_area},
                severity=Severity.HIGH,
                message=f"Bounding box area must be at least {min_area} pixels"
            ))
        
        # Pattern for IOU threshold
        iou_match = re.search(r'Maximum IOU between boxes: ([\d.]+)', text)
        if iou_match:
            iou = float(iou_match.group(1))
            rules.append(Rule(
                name="bbox_max_iou",
                rule_type=RuleType.BBOX_IOU,
                params={"max_iou": iou},
                severity=Severity.CRITICAL,
                message=f"Bounding boxes must not overlap more than {iou}"
            ))
        
        # Pattern for aspect ratio
        aspect_max_match = re.search(r'Maximum aspect ratio: ([\d.]+)', text)
        aspect_min_match = re.search(r'Minimum aspect ratio: ([\d.]+)', text)
        if aspect_max_match and aspect_min_match:
            max_ratio = float(aspect_max_match.group(1))
            min_ratio = float(aspect_min_match.group(1))
            rules.append(Rule(
                name="bbox_aspect_ratio",
                rule_type=RuleType.BBOX_ASPECT_RATIO,
                params={"min_ratio": min_ratio, "max_ratio": max_ratio},
                severity=Severity.MEDIUM,
                message=f"Bounding box aspect ratio must be between {min_ratio} and {max_ratio}"
            ))
        
        return rules
    
    @staticmethod
    def parse_json(json_data: Union[str, Dict]) -> RuleSet:
        """Parse JSON guidelines."""
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        name = data.get("name", "Unnamed Rule Set")
        version = data.get("version", "1.0")
        description = data.get("description", "")
        
        rules = []
        for rule_data in data.get("rules", []):
            rule = Rule(
                name=rule_data.get("name", "Unnamed Rule"),
                rule_type=RuleType(rule_data.get("type", "custom")),
                params=rule_data.get("params", {}),
                severity=Severity(rule_data.get("severity", Severity.MEDIUM.value)),
                message=rule_data.get("message", "QC Rule Failed"),
                description=rule_data.get("description", "")
            )
            rules.append(rule)
        
        return RuleSet(
            name=name,
            version=version,
            description=description,
            rules=rules
        )
    
    @staticmethod
    def parse_xml(xml_data: Union[str, bytes]) -> RuleSet:
        """Parse XML guidelines."""
        if isinstance(xml_data, str):
            root = ET.fromstring(xml_data)
        else:
            root = ET.fromstring(xml_data.decode('utf-8'))
        
        name = root.find('name').text if root.find('name') is not None else "Unnamed Rule Set"
        version = root.find('version').text if root.find('version') is not None else "1.0"
        description = root.find('description').text if root.find('description') is not None else ""
        
        rules = []
        for rule_elem in root.findall('rules/rule'):
            rule = Rule(
                name=rule_elem.find('name').text if rule_elem.find('name') is not None else "Unnamed Rule",
                rule_type=RuleType(rule_elem.find('type').text if rule_elem.find('type') is not None else "custom"),
                params={param_elem.tag: param_elem.text for param_elem in rule_elem.findall('params/param')},
                severity=Severity(rule_elem.find('severity').text if rule_elem.find('severity') is not None else Severity.MEDIUM.value),
                message=rule_elem.find('message').text if rule_elem.find('message') is not None else "QC Rule Failed",
                description=rule_elem.find('description').text if rule_elem.find('description') is not None else ""
            )
            rules.append(rule)
        
        return RuleSet(
            name=name,
            version=version,
            description=description,
            rules=rules
        )
    
    @staticmethod
    def parse_markdown(md_text: str) -> RuleSet:
        """Parse Markdown guidelines."""
        # Convert markdown to text and parse
        text = md_text
        
        # Remove markdown headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^-\s+', '', text, flags=re.MULTILINE)
        
        rules = GuidelineParser.parse_text(text)
        
        return RuleSet(
            name="Markdown Guidelines",
            version="1.0",
            description="Parsed from Markdown",
            rules=rules
        )
    
    @classmethod
    def parse(cls, content: Union[str, Dict, bytes], content_type: str = "text") -> RuleSet:
        """
        Parse guideline content based on type.
        
        Args:
            content: Guideline content
            content_type: Type of content (text, json, xml, markdown)
            
        Returns:
            RuleSet with parsed rules
        """
        parsers = {
            "text": lambda c: RuleSet(name="Text Guidelines", version="1.0", rules=cls.parse_text(c)),
            "json": lambda c: cls.parse_json(c),
            "xml": lambda c: cls.parse_xml(c),
            "markdown": lambda c: cls.parse_markdown(c)
        }
        
        parser = parsers.get(content_type.lower(), parsers["text"])
        return parser(content)
```

---

### 4.2 Rule Set Management

**Duration:** Week 1 (Day 4-5)  
**Owner:** Backend Dev  
**Estimate:** 2 days

#### Tasks
| ID | Task | Description | Estimate |
|----|------|-------------|----------|
| RS-01 | Rule set CRUD API | Create, read, update, delete rule sets | 1 day |
| RS-02 | Rule set versioning | Version control for rule sets | 1 day |
| RS-03 | Rule set activation | Enable/disable rule sets | 0.5 day |
| RS-04 | Rule set to project mapping | Assign rule sets to CVAT projects | 0.5 day |

#### Models

```python
# src/models/rule.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class RuleType(str, Enum):
    BBOX_MIN_AREA = "bbox_min_area"
    BBOX_MAX_AREA = "bbox_max_area"
    BBOX_IOU = "bbox_iou"
    BBOX_ASPECT_RATIO = "bbox_aspect_ratio"
    POLYGON_MIN_POINTS = "polygon_min_points"
    POLYGON_MAX_POINTS = "polygon_max_points"
    LABEL_CONSISTENCY = "label_consistency"
    DUPLICATE_DETECTION = "duplicate_detection"
    CUSTOM_SCRIPT = "custom_script"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Rule(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., description="Rule name")
    rule_type: RuleType = Field(..., description="Rule type")
    params: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    severity: Severity = Field(default=Severity.MEDIUM, description="Rule severity")
    message: str = Field(..., description="Error message")
    description: Optional[str] = Field(None, description="Rule description")
    is_active: bool = Field(default=True, description="Whether rule is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RuleSet(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., description="Rule set name")
    version: str = Field(default="1.0", description="Rule set version")
    description: Optional[str] = Field(None, description="Rule set description")
    rules: List[Rule] = Field(default_factory=list, description="List of rules")
    is_active: bool = Field(default=True, description="Whether rule set is active")
    is_default: bool = Field(default=False, description="Whether this is the default rule set")
    project_ids: List[int] = Field(default_factory=list, description="CVAT project IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RuleSetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rules: List[Rule]
    is_active: bool = True

class RuleSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[List[Rule]] = None
    is_active: Optional[bool] = None
    project_ids: Optional[List[int]] = None
```

#### API Endpoints

```python
# src/app/api/v1/routers/rule_sets.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.rule import (
    RuleSet, RuleSetCreate, RuleSetUpdate, Rule
)
from src.services.rule_set_service import RuleSetService
from src.app.dependencies import get_db

router = APIRouter(prefix="/api/v1/rule-sets", tags=["rule-sets"])


@router.get("/", response_model=List[RuleSet])
async def list_rule_sets(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    db: Session = Depends(get_db)
):
    """List all rule sets."""
    service = RuleSetService(db)
    return service.list_rule_sets(is_active, is_default)


@router.get("/{rule_set_id}", response_model=RuleSet)
async def get_rule_set(rule_set_id: int, db: Session = Depends(get_db)):
    """Get a rule set by ID."""
    service = RuleSetService(db)
    rule_set = service.get_rule_set(rule_set_id)
    if not rule_set:
        raise HTTPException(status_code=404, detail="Rule set not found")
    return rule_set


@router.post("/", response_model=RuleSet, status_code=201)
async def create_rule_set(
    rule_set_data: RuleSetCreate,
    db: Session = Depends(get_db)
):
    """Create a new rule set."""
    service = RuleSetService(db)
    return service.create_rule_set(rule_set_data)


@router.put("/{rule_set_id}", response_model=RuleSet)
async def update_rule_set(
    rule_set_id: int,
    rule_set_data: RuleSetUpdate,
    db: Session = Depends(get_db)
):
    """Update a rule set."""
    service = RuleSetService(db)
    rule_set = service.update_rule_set(rule_set_id, rule_set_data)
    if not rule_set:
        raise HTTPException(status_code=404, detail="Rule set not found")
    return rule_set


@router.delete("/{rule_set_id}", status_code=204)
async def delete_rule_set(rule_set_id: int, db: Session = Depends(get_db)):
    """Delete a rule set."""
    service = RuleSetService(db)
    if not service.delete_rule_set(rule_set_id):
        raise HTTPException(status_code=404, detail="Rule set not found")
    return None


@router.post("/parse", response_model=RuleSet)
async def parse_guidelines(
    content: str = Query(..., description="Guideline content"),
    content_type: str = Query(default="text", description="Content type (text, json, xml, markdown)"),
    db: Session = Depends(get_db)
):
    """Parse guidelines and create a rule set."""
    service = RuleSetService(db)
    return service.parse_guidelines(content, content_type)


@router.post("/{rule_set_id}/assign-projects", response_model=RuleSet)
async def assign_projects(
    rule_set_id: int,
    project_ids: List[int],
    db: Session = Depends(get_db)
):
    """Assign rule set to projects."""
    service = RuleSetService(db)
    rule_set = service.assign_projects(rule_set_id, project_ids)
    if not rule_set:
        raise HTTPException(status_code=404, detail="Rule set not found")
    return rule_set
```

#### Service Layer

```python
# src/services/rule_set_service.py
from typing import Optional, List
from sqlalchemy.orm import Session

from database.schemas.rule_set import RuleSet as RuleSetDB
from database.schemas.rule import Rule as RuleDB
from src.models.rule import RuleSet, RuleSetCreate, RuleSetUpdate, Rule
from src.rules.parsers.guideline_parser import GuidelineParser


class RuleSetService:
    """Service for managing rule sets."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_rule_sets(self, is_active: Optional[bool] = None, 
                       is_default: Optional[bool] = None) -> List[RuleSet]:
        """List all rule sets."""
        query = self.db.query(RuleSetDB)
        if is_active is not None:
            query = query.filter(RuleSetDB.is_active == is_active)
        if is_default is not None:
            query = query.filter(RuleSetDB.is_default == is_default)
        
        rule_sets = query.all()
        return [self._db_to_model(rs) for rs in rule_sets]
    
    def get_rule_set(self, rule_set_id: int) -> Optional[RuleSet]:
        """Get a rule set by ID."""
        rule_set = self.db.query(RuleSetDB).filter(
            RuleSetDB.id == rule_set_id
        ).first()
        return self._db_to_model(rule_set) if rule_set else None
    
    def create_rule_set(self, rule_set_data: RuleSetCreate) -> RuleSet:
        """Create a new rule set."""
        # Check if name already exists
        existing = self.db.query(RuleSetDB).filter(
            RuleSetDB.name == rule_set_data.name
        ).first()
        if existing:
            raise ValueError(f"Rule set with name '{rule_set_data.name}' already exists")
        
        # Create rule set in database
        rule_set = RuleSetDB(
            name=rule_set_data.name,
            description=rule_set_data.description or "",
            is_active=rule_set_data.is_active,
            is_default=False
        )
        self.db.add(rule_set)
        self.db.commit()
        self.db.refresh(rule_set)
        
        # Create rules
        for rule_data in rule_set_data.rules:
            rule = RuleDB(
                name=rule_data.name,
                rule_type=rule_data.rule_type.value,
                params=rule_data.params,
                severity=rule_data.severity.value,
                message=rule_data.message,
                description=rule_data.description or "",
                is_active=True,
                rule_set_id=rule_set.id
            )
            self.db.add(rule)
        
        self.db.commit()
        
        return self._db_to_model(rule_set)
    
    def update_rule_set(self, rule_set_id: int, rule_set_data: RuleSetUpdate) -> Optional[RuleSet]:
        """Update a rule set."""
        rule_set = self.db.query(RuleSetDB).filter(
            RuleSetDB.id == rule_set_id
        ).first()
        
        if not rule_set:
            return None
        
        if rule_set_data.name:
            rule_set.name = rule_set_data.name
        if rule_set_data.description:
            rule_set.description = rule_set_data.description
        if rule_set_data.is_active is not None:
            rule_set.is_active = rule_set_data.is_active
        if rule_set_data.project_ids is not None:
            rule_set.project_ids = rule_set_data.project_ids
        
        rule_set.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule_set)
        
        return self._db_to_model(rule_set)
    
    def delete_rule_set(self, rule_set_id: int) -> bool:
        """Delete a rule set."""
        rule_set = self.db.query(RuleSetDB).filter(
            RuleSetDB.id == rule_set_id
        ).first()
        
        if not rule_set:
            return False
        
        self.db.delete(rule_set)
        self.db.commit()
        return True
    
    def assign_projects(self, rule_set_id: int, project_ids: List[int]) -> Optional[RuleSet]:
        """Assign rule set to projects."""
        rule_set = self.db.query(RuleSetDB).filter(
            RuleSetDB.id == rule_set_id
        ).first()
        
        if not rule_set:
            return None
        
        rule_set.project_ids = project_ids
        rule_set.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule_set)
        
        return self._db_to_model(rule_set)
    
    def parse_guidelines(self, content: str, content_type: str) -> RuleSet:
        """Parse guidelines and create a rule set."""
        rule_set = GuidelineParser.parse(content, content_type)
        
        # Create in database
        db_rule_set = RuleSetDB(
            name=rule_set.name,
            version=rule_set.version,
            description=rule_set.description or "",
            is_active=True,
            is_default=False
        )
        self.db.add(db_rule_set)
        self.db.commit()
        self.db.refresh(db_rule_set)
        
        # Create rules
        for rule in rule_set.rules:
            db_rule = RuleDB(
                name=rule.name,
                rule_type=rule.rule_type.value,
                params=rule.params,
                severity=rule.severity.value,
                message=rule.message,
                description=rule.description or "",
                is_active=True,
                rule_set_id=db_rule_set.id
            )
            self.db.add(db_rule)
        
        self.db.commit()
        
        return self._db_to_model(db_rule_set)
    
    def _db_to_model(self, rule_set: RuleSetDB) -> RuleSet:
        """Convert database model to response model."""
        return RuleSet(
            id=rule_set.id,
            name=rule_set.name,
            version=rule_set.version,
            description=rule_set.description,
            rules=[self._rule_db_to_model(rule) for rule in rule_set.rules],
            is_active=rule_set.is_active,
            is_default=rule_set.is_default,
            project_ids=rule_set.project_ids or [],
            created_at=rule_set.created_at,
            updated_at=rule_set.updated_at
        )
    
    def _rule_db_to_model(self, rule: RuleDB) -> Rule:
        """Convert rule database model to response model."""
        return Rule(
            id=rule.id,
            name=rule.name,
            rule_type=RuleType(rule.rule_type),
            params=rule.params or {},
            severity=Severity(rule.severity),
            message=rule.message,
            description=rule.description,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
```

---

### 4.3 Custom Rule Support

**Duration:** Week 2 (Day 6-10)  
**Owner:** Backend Dev  
**Estimate:** 5 days

#### Tasks
| ID | Task | Description | Estimate |
|----|------|-------------|----------|
| CR-01 | Python script-based rules | Support custom Python rules | 2 days |
| CR-02 | Rule validation & sandboxing | Security for custom rules | 2 days |
| CR-03 | Rule execution with timeout | Prevent infinite loops | 2 days |
| CR-04 | Rule error handling | Graceful failure | 1 day |

#### Custom Rule Implementation

```python
# src/rules/custom_rule_engine.py
import importlib
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from contextlib import contextmanager
import signal

from src.models.frame import Frame, Annotation
from src.models.rule import Rule


class CustomRuleError(Exception):
    """Custom exception for custom rule errors."""
    pass


class CustomRuleTimeoutError(CustomRuleError):
    """Exception for rule timeout."""
    pass


class CustomRuleEngine:
    """Engine for executing custom Python rules."""
    
    def __init__(self, custom_rules_dir: str = "src/rules/custom"):
        self.custom_rules_dir = Path(custom_rules_dir)
        self.custom_rules_cache: Dict[str, Callable] = {}
        self.max_execution_time = 5.0  # seconds
        
        # Ensure custom rules directory exists
        self.custom_rules_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all custom rules
        self._load_custom_rules()
    
    def _load_custom_rules(self):
        """Load all custom rule scripts from directory."""
        self.custom_rules_cache = {}
        
        if self.custom_rules_dir.exists():
            for rule_file in self.custom_rules_dir.glob("*.py"):
                module_name = rule_file.stem
                if module_name not in self.custom_rules_cache:
                    self._load_custom_rule(rule_file, module_name)
    
    def _load_custom_rule(self, rule_file: Path, module_name: str):
        """Load a single custom rule script."""
        try:
            spec = importlib.util.spec_from_file_location(
                module_name, rule_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "validate_annotation"):
                    self.custom_rules_cache[module_name] = module.validate_annotation
                elif hasattr(module, "validate_frame"):
                    self.custom_rules_cache[module_name] = module.validate_frame
        except Exception as e:
            print(f"Failed to load custom rule {module_name}: {e}")
            traceback.print_exc()
    
    def _get_rule_function(self, rule: Rule) -> Optional[Callable]:
        """Get the rule function from cache."""
        if rule.rule_type == RuleType.CUSTOM_SCRIPT:
            return self.custom_rules_cache.get(rule.name)
        return None
    
    @contextmanager
    def _timeout_handler(self):
        """Context manager for handling timeouts."""
        def timeout_handler(signum, frame):
            raise CustomRuleTimeoutError(
                f"Rule execution timed out after {self.max_execution_time}s"
            )
        
        # Set signal handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.max_execution_time))
        
        try:
            yield
        finally:
            signal.alarm(0)  # Cancel alarm
            signal.signal(signal.SIGALRM, old_handler)
    
    def execute_rule(self, rule: Rule, annotation: Annotation, 
                     frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute a custom rule on an annotation.
        
        Args:
            rule: Rule to execute
            annotation: Annotation to validate
            frame: Frame containing the annotation
            context: Additional context
            
        Returns:
            List of error dictionaries
        """
        if rule.rule_type != RuleType.CUSTOM_SCRIPT:
            return []
        
        rule_func = self._get_rule_function(rule)
        if not rule_func:
            return [{
                "type": "custom_rule_not_found",
                "message": f"Custom rule '{rule.name}' not found",
                "severity": Severity.ERROR.value
            }]
        
        try:
            with self._timeout_handler():
                start_time = time.time()
                errors = rule_func(annotation, frame, context)
                execution_time = time.time() - start_time
                
                if not isinstance(errors, list):
                    errors = [errors] if errors else []
                
                return errors
        except CustomRuleTimeoutError:
            return [{
                "type": "custom_rule_timeout",
                "message": f"Custom rule '{rule.name}' timed out",
                "severity": Severity.CRITICAL.value
            }]
        except Exception as e:
            return [{
                "type": "custom_rule_error",
                "message": f"Custom rule '{rule.name}' failed: {str(e)}",
                "severity": Severity.CRITICAL.value,
                "details": {"error": str(e), "traceback": traceback.format_exc()}
            }]
    
    def add_custom_rule(self, rule_name: str, rule_code: str) -> bool:
        """
        Add a new custom rule dynamically.
        
        Args:
            rule_name: Name of the rule
            rule_code: Python code for the rule
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create rule file
            rule_file = self.custom_rules_dir / f"{rule_name}.py"
            
            # Write code with proper validation function
            full_code = f"""
{rule_code}


def validate_annotation(annotation, frame, context):
    '''Default validation function for custom rules.'''
    # Your validation logic here
    errors = []
    # Example: errors.append({{"type": "custom", "message": "Error message", "severity": "high"}})
    return errors
"""
            
            with open(rule_file, 'w') as f:
                f.write(full_code)
            
            # Reload rules
            self._load_custom_rules()
            
            return rule_name in self.custom_rules_cache
            
        except Exception as e:
            print(f"Failed to add custom rule {rule_name}: {e}")
            return False
    
    def remove_custom_rule(self, rule_name: str) -> bool:
        """
        Remove a custom rule.
        
        Args:
            rule_name: Name of the rule
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rule_file = self.custom_rules_dir / f"{rule_name}.py"
            if rule_file.exists():
                rule_file.unlink()
                self.custom_rules_cache.pop(rule_name, None)
                return True
            return False
        except Exception as e:
            print(f"Failed to remove custom rule {rule_name}: {e}")
            return False
    
    def list_custom_rules(self) -> List[str]:
        """List all custom rule names."""
        return list(self.custom_rules_cache.keys())
```

#### Custom Rule Example

```python
# src/rules/custom/car_bbox_check.py
from typing import Dict, Any, List
from letmeqc.models.frame import Frame, Annotation


def validate_annotation(annotation: Annotation, frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Custom validation rule: Check if car bbox has minimum width of 50
    
    Args:
        annotation: Current annotation to validate
        frame: Frame containing the annotation
        context: Additional context (job info, other annotations, etc.)
    
    Returns:
        List of errors, each error is a dict with:
        - type: str
        - message: str
        - severity: str (low, medium, high, critical)
        - details: dict (optional)
    """
    errors = []
    
    # Example: Check if car bbox has minimum width
    if annotation.label == "car":
        if annotation.bbox.width < 50:
            errors.append({
                "type": "custom_car_width",
                "message": f"Car bbox width {annotation.bbox.width} is less than 50",
                "severity": "high",
                "details": {
                    "expected": 50,
                    "actual": annotation.bbox.width,
                    "label": annotation.label
                }
            })
        
        # Check if car bbox is too tall
        if annotation.bbox.height > annotation.bbox.width * 2:
            errors.append({
                "type": "custom_car_height",
                "message": f"Car bbox height {annotation.bbox.height} is more than 2x width",
                "severity": "medium",
                "details": {
                    "height": annotation.bbox.height,
                    "width": annotation.bbox.width,
                    "ratio": annotation.bbox.height / annotation.bbox.width
                }
            })
    
    return errors
```

---

### 4.4 Enhanced Rule Engine

**Duration:** Week 3 (Day 11-15)  
**Owner:** Backend Dev  
**Estimate:** 5 days

#### Tasks
| ID | Task | Description | Estimate |
|----|------|-------------|----------|
| RE-01 | Rule engine service | Core rule execution logic | 2 days |
| RE-02 | Rule execution pipeline | Execute rules in order | 2 days |
| RE-03 | Rule result aggregation | Combine results from all rules | 2 days |
| RE-04 | Performance optimization | Optimize rule execution | 2 days |

#### Rule Engine Service

```python
# src/rules/rule_engine.py
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time
import logging
from pathlib import Path

from src.models.frame import Frame, Annotation
from src.models.rule import Rule, RuleSet, RuleType, Severity
from src.rules.custom_rule_engine import CustomRuleEngine

logger = logging.getLogger(__name__)


@dataclass
class RuleResult:
    rule_id: Optional[int]
    rule_name: str
    rule_type: RuleType
    passed: bool
    errors: List[Dict[str, Any]]
    execution_time: float
    severity: Severity


class RuleEngine:
    """Main rule engine for executing QC rules."""
    
    def __init__(self):
        self.custom_rule_engine = CustomRuleEngine()
        self.builtin_rule_handlers = {
            RuleType.BBOX_MIN_AREA: self._handle_bbox_min_area,
            RuleType.BBOX_MAX_AREA: self._handle_bbox_max_area,
            RuleType.BBOX_IOU: self._handle_bbox_iou,
            RuleType.BBOX_ASPECT_RATIO: self._handle_bbox_aspect_ratio,
            RuleType.POLYGON_MIN_POINTS: self._handle_polygon_min_points,
            RuleType.POLYGON_MAX_POINTS: self._handle_polygon_max_points,
            RuleType.LABEL_CONSISTENCY: self._handle_label_consistency,
            RuleType.DUPLICATE_DETECTION: self._handle_duplicate_detection,
            RuleType.CUSTOM_SCRIPT: self._handle_custom_script
        }
    
    def get_active_rules(self, project_id: Optional[int] = None) -> List[Rule]:
        """Get all active rules for a project."""
        # This would query the database for active rules
        # For now, return default rules
        from src.rules.default_rules import DEFAULT_RULES
        return DEFAULT_RULES
    
    def execute_rule(self, rule: Rule, annotation: Annotation, 
                     frame: Frame, context: Dict[str, Any]) -> RuleResult:
        """
        Execute a single rule on an annotation.
        
        Args:
            rule: Rule to execute
            annotation: Annotation to validate
            frame: Frame containing the annotation
            context: Additional context
            
        Returns:
            RuleResult with execution details
        """
        start_time = time.time()
        errors = []
        
        try:
            # Get handler for rule type
            handler = self.builtin_rule_handlers.get(rule.rule_type)
            
            if handler:
                # Execute built-in rule
                errors = handler(rule, annotation, frame, context)
            else:
                # Execute custom rule
                errors = self.custom_rule_engine.execute_rule(rule, annotation, frame, context)
            
            execution_time = time.time() - start_time
            
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                passed=len(errors) == 0,
                errors=errors,
                execution_time=execution_time,
                severity=rule.severity
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed to execute rule {rule.name}: {e}")
            
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                passed=False,
                errors=[{
                    "type": "rule_execution_error",
                    "message": f"Rule execution failed: {str(e)}",
                    "severity": Severity.CRITICAL.value
                }],
                execution_time=execution_time,
                severity=Severity.CRITICAL
            )
    
    def run_qc(self, frames: List[Frame], project_id: Optional[int] = None, 
               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run QC on all frames with active rules.
        
        Args:
            frames: List of frames to validate
            project_id: Optional project ID for rule filtering
            context: Additional context for rules
            
        Returns:
            Dictionary with QC results
        """
        results = {
            "total_frames": len(frames),
            "total_annotations": 0,
            "total_errors": 0,
            "frame_results": [],
            "rule_results": [],
            "execution_time": 0
        }
        
        start_time = time.time()
        active_rules = self.get_active_rules(project_id)
        context = context or {}
        
        for frame in frames:
            frame_result = {
                "frame_index": frame.index,
                "annotation_results": []
            }
            
            for annotation in frame.annotations:
                results["total_annotations"] += 1
                annotation_result = {
                    "annotation_id": annotation.id,
                    "label": annotation.label,
                    "rule_results": []
                }
                
                for rule in active_rules:
                    rule_result = self.execute_rule(rule, annotation, frame, context)
                    annotation_result["rule_results"].append(rule_result.__dict__)
                    
                    if not rule_result.passed:
                        results["total_errors"] += len(rule_result.errors)
                        results["rule_results"].append(rule_result.__dict__)
                
                frame_result["annotation_results"].append(annotation_result)
            
            results["frame_results"].append(frame_result)
        
        results["execution_time"] = time.time() - start_time
        return results
    
    # ==================== BUILT-IN RULE HANDLERS ====================
    
    def _handle_bbox_min_area(self, rule: Rule, annotation: Annotation, 
                              frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle bbox min area rule."""
        errors = []
        min_area = rule.params.get("min_area", 100)
        
        if hasattr(annotation, 'bbox') and annotation.bbox:
            bbox_area = annotation.bbox.width * annotation.bbox.height
            if bbox_area < min_area:
                errors.append({
                    "type": "bbox_min_area",
                    "message": f"Bounding box area {bbox_area} < {min_area}",
                    "severity": rule.severity.value,
                    "details": {
                        "expected": min_area,
                        "actual": bbox_area,
                        "width": annotation.bbox.width,
                        "height": annotation.bbox.height
                    }
                })
        
        return errors
    
    def _handle_bbox_max_area(self, rule: Rule, annotation: Annotation, 
                              frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle bbox max area rule."""
        errors = []
        max_area = rule.params.get("max_area", 10000)
        
        if hasattr(annotation, 'bbox') and annotation.bbox:
            bbox_area = annotation.bbox.width * annotation.bbox.height
            if bbox_area > max_area:
                errors.append({
                    "type": "bbox_max_area",
                    "message": f"Bounding box area {bbox_area} > {max_area}",
                    "severity": rule.severity.value,
                    "details": {
                        "expected_max": max_area,
                        "actual": bbox_area,
                        "width": annotation.bbox.width,
                        "height": annotation.bbox.height
                    }
                })
        
        return errors
    
    def _handle_bbox_iou(self, rule: Rule, annotation: Annotation, 
                        frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle bbox IOU rule."""
        errors = []
        max_iou = rule.params.get("max_iou", 0.95)
        duplicate_threshold = rule.params.get("duplicate_threshold", 0.98)
        
        if hasattr(annotation, 'bbox') and annotation.bbox:
            # Get all other bounding boxes in the frame
            other_boxes = [
                a.bbox for a in frame.annotations 
                if a.id != annotation.id and hasattr(a, 'bbox') and a.bbox
            ]
            
            for other_box in other_boxes:
                iou = annotation.bbox.calculate_iou(other_box)
                
                if iou > duplicate_threshold:
                    errors.append({
                        "type": "duplicate_bbox",
                        "message": f"Duplicate bbox detected (IOU: {iou:.2f})",
                        "severity": Severity.CRITICAL.value,
                        "details": {
                            "iou": iou,
                            "other_bbox_id": other_box.id,
                            "other_bbox": {
                                "x": other_box.x,
                                "y": other_box.y,
                                "width": other_box.width,
                                "height": other_box.height
                            }
                        }
                    })
                elif iou > max_iou:
                    errors.append({
                        "type": "high_overlap",
                        "message": f"High overlap with other bbox (IOU: {iou:.2f})",
                        "severity": rule.severity.value,
                        "details": {
                            "iou": iou,
                            "other_bbox_id": other_box.id,
                            "other_bbox": {
                                "x": other_box.x,
                                "y": other_box.y,
                                "width": other_box.width,
                                "height": other_box.height
                            }
                        }
                    })
        
        return errors
    
    def _handle_bbox_aspect_ratio(self, rule: Rule, annotation: Annotation, 
                                  frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle bbox aspect ratio rule."""
        errors = []
        min_ratio = rule.params.get("min_ratio", 0.1)
        max_ratio = rule.params.get("max_ratio", 10.0)
        
        if hasattr(annotation, 'bbox') and annotation.bbox:
            width = annotation.bbox.width
            height = annotation.bbox.height
            
            if width > 0 and height > 0:
                ratio = width / height
                
                if ratio < min_ratio or ratio > max_ratio:
                    errors.append({
                        "type": "bbox_aspect_ratio",
                        "message": f"Bounding box aspect ratio {ratio:.2f} out of range [{min_ratio}, {max_ratio}]",
                        "severity": rule.severity.value,
                        "details": {
                            "min_ratio": min_ratio,
                            "max_ratio": max_ratio,
                            "actual_ratio": ratio,
                            "width": width,
                            "height": height
                        }
                    })
        
        return errors
    
    def _handle_polygon_min_points(self, rule: Rule, annotation: Annotation, 
                                    frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle polygon min points rule."""
        errors = []
        min_points = rule.params.get("min_points", 3)
        
        if hasattr(annotation, 'polygon') and annotation.polygon:
            if len(annotation.polygon.points) < min_points:
                errors.append({
                    "type": "polygon_min_points",
                    "message": f"Polygon has {len(annotation.polygon.points)} points < {min_points}",
                    "severity": rule.severity.value,
                    "details": {
                        "expected_min": min_points,
                        "actual": len(annotation.polygon.points)
                    }
                })
        
        return errors
    
    def _handle_polygon_max_points(self, rule: Rule, annotation: Annotation, 
                                    frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle polygon max points rule."""
        errors = []
        max_points = rule.params.get("max_points", 1000)
        
        if hasattr(annotation, 'polygon') and annotation.polygon:
            if len(annotation.polygon.points) > max_points:
                errors.append({
                    "type": "polygon_max_points",
                    "message": f"Polygon has {len(annotation.polygon.points)} points > {max_points}",
                    "severity": rule.severity.value,
                    "details": {
                        "expected_max": max_points,
                        "actual": len(annotation.polygon.points)
                    }
                })
        
        return errors
    
    def _handle_label_consistency(self, rule: Rule, annotation: Annotation, 
                                  frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle label consistency rule."""
        errors = []
        allowed_labels = rule.params.get("allowed_labels", [])
        
        if allowed_labels and annotation.label not in allowed_labels:
            errors.append({
                "type": "label_not_allowed",
                "message": f"Label '{annotation.label}' is not in allowed list: {allowed_labels}",
                "severity": rule.severity.value,
                "details": {
                    "allowed_labels": allowed_labels,
                    "actual_label": annotation.label
                }
            })
        
        return errors
    
    def _handle_duplicate_detection(self, rule: Rule, annotation: Annotation, 
                                    frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle duplicate detection rule (for polygons)."""
        errors = []
        iou_threshold = rule.params.get("iou_threshold", 0.95)
        
        if hasattr(annotation, 'polygon') and annotation.polygon:
            # Check for duplicate polygons
            for other_annotation in frame.annotations:
                if other_annotation.id != annotation.id and hasattr(other_annotation, 'polygon'):
                    iou = annotation.polygon.calculate_iou(other_annotation.polygon)
                    if iou > iou_threshold:
                        errors.append({
                            "type": "duplicate_polygon",
                            "message": f"Duplicate polygon detected (IOU: {iou:.2f})",
                            "severity": rule.severity.value,
                            "details": {
                                "iou": iou,
                                "other_annotation_id": other_annotation.id
                            }
                        })
        
        return errors
    
    def _handle_custom_script(self, rule: Rule, annotation: Annotation, 
                              frame: Frame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle custom script rule."""
        # Delegate to custom rule engine
        return self.custom_rule_engine.execute_rule(rule, annotation, frame, context)
```

---

### 4.5 Default Rules

```python
# src/rules/default_rules.py
from src.models.rule import Rule, RuleType, Severity

DEFAULT_RULES = [
    Rule(
        id=1,
        name="bbox_min_area",
        rule_type=RuleType.BBOX_MIN_AREA,
        params={"min_area": 100},
        severity=Severity.MEDIUM,
        message="Bounding box area is too small",
        description="Checks if bounding box area meets minimum requirement"
    ),
    Rule(
        id=2,
        name="bbox_max_area",
        rule_type=RuleType.BBOX_MAX_AREA,
        params={"max_area": 1000000},
        severity=Severity.LOW,
        message="Bounding box area is too large",
        description="Checks if bounding box area exceeds maximum limit"
    ),
    Rule(
        id=3,
        name="bbox_overlap",
        rule_type=RuleType.BBOX_IOU,
        params={"max_iou": 0.95, "duplicate_threshold": 0.98},
        severity=Severity.HIGH,
        message="Bounding boxes overlap too much",
        description="Checks for overlapping bounding boxes"
    ),
    Rule(
        id=4,
        name="bbox_aspect_ratio",
        rule_type=RuleType.BBOX_ASPECT_RATIO,
        params={"min_ratio": 0.1, "max_ratio": 10.0},
        severity=Severity.MEDIUM,
        message="Bounding box aspect ratio is out of range",
        description="Checks if bounding box aspect ratio is within valid range"
    ),
    Rule(
        id=5,
        name="polygon_min_points",
        rule_type=RuleType.POLYGON_MIN_POINTS,
        params={"min_points": 3},
        severity=Severity.MEDIUM,
        message="Polygon has too few points",
        description="Checks if polygon has minimum required points"
    ),
    Rule(
        id=6,
        name="polygon_max_points",
        rule_type=RuleType.POLYGON_MAX_POINTS,
        params={"max_points": 1000},
        severity=Severity.LOW,
        message="Polygon has too many points",
        description="Checks if polygon has too many points"
    ),
    Rule(
        id=7,
        name="duplicate_detection",
        rule_type=RuleType.DUPLICATE_DETECTION,
        params={"iou_threshold": 0.95},
        severity=Severity.CRITICAL,
        message="Duplicate annotation detected",
        description="Detects duplicate annotations based on IOU"
    )
]
```

---

## 🧪 Testing

### Unit Tests

```python
# tests/unit/test_rule_engine.py
import pytest
from src.rules.rule_engine import RuleEngine
from src.models.frame import Frame, Bbox, Polygon, Annotation
from src.models.rule import Rule, RuleType, Severity


@pytest.fixture
def rule_engine():
    return RuleEngine()


@pytest.fixture
def sample_frame():
    bbox1 = Bbox(x=10, y=20, width=100, height=50)
    bbox2 = Bbox(x=10, y=20, width=100, height=50)  # Same as bbox1
    bbox3 = Bbox(x=200, y=200, width=50, height=100)
    
    return Frame(
        index=0,
        width=800,
        height=600,
        annotations=[
            Annotation(id=1, label="car", bbox=bbox1),
            Annotation(id=2, label="car", bbox=bbox2),
            Annotation(id=3, label="person", bbox=bbox3)
        ]
    )


class TestRuleEngine:
    def test_bbox_min_area_pass(self, rule_engine, sample_frame):
        rule = Rule(
            id=1,
            name="test_min_area",
            rule_type=RuleType.BBOX_MIN_AREA,
            params={"min_area": 1000},
            severity=Severity.MEDIUM,
            message="Test"
        )
        
        result = rule_engine.execute_rule(rule, sample_frame.annotations[0], sample_frame, {})
        assert result.passed == True
        assert len(result.errors) == 0
    
    def test_bbox_min_area_fail(self, rule_engine, sample_frame):
        rule = Rule(
            id=1,
            name="test_min_area",
            rule_type=RuleType.BBOX_MIN_AREA,
            params={"min_area": 10000},
            severity=Severity.MEDIUM,
            message="Test"
        )
        
        result = rule_engine.execute_rule(rule, sample_frame.annotations[0], sample_frame, {})
        assert result.passed == False
        assert len(result.errors) == 1
        assert result.errors[0]["type"] == "bbox_min_area"
    
    def test_bbox_iou_duplicate(self, rule_engine, sample_frame):
        rule = Rule(
            id=1,
            name="test_iou",
            rule_type=RuleType.BBOX_IOU,
            params={"max_iou": 0.95, "duplicate_threshold": 0.98},
            severity=Severity.HIGH,
            message="Test"
        )
        
        # Test with first annotation (has duplicate at index 1)
        result = rule_engine.execute_rule(rule, sample_frame.annotations[0], sample_frame, {})
        assert result.passed == False
        assert len(result.errors) >= 1
        assert any(e["type"] == "duplicate_bbox" for e in result.errors)
    
    def test_bbox_aspect_ratio(self, rule_engine, sample_frame):
        rule = Rule(
            id=1,
            name="test_aspect_ratio",
            rule_type=RuleType.BBOX_ASPECT_RATIO,
            params={"min_ratio": 0.5, "max_ratio": 2.0},
            severity=Severity.MEDIUM,
            message="Test"
        )
        
        # Annotation 0: 100x50 -> ratio = 2.0 (should pass)
        result = rule_engine.execute_rule(rule, sample_frame.annotations[0], sample_frame, {})
        assert result.passed == True
        
        # Annotation 2: 50x100 -> ratio = 0.5 (should pass)
        result = rule_engine.execute_rule(rule, sample_frame.annotations[2], sample_frame, {})
        assert result.passed == True
    
    def test_run_qc(self, rule_engine, sample_frame):
        frames = [sample_frame]
        result = rule_engine.run_qc(frames, context={"test": True})
        
        assert result["total_frames"] == 1
        assert result["total_annotations"] == 3
        assert "execution_time" in result
        assert len(result["frame_results"]) == 1
```

---

## ✅ Acceptance Criteria

Phase 4 is **complete** when:

1. ✅ Guideline parser supports text, JSON, XML, Markdown
2. ✅ Rule set CRUD API implemented
3. ✅ Rule set versioning and activation working
4. ✅ Custom rule execution engine implemented
5. ✅ Custom rules can be added/removed dynamically
6. ✅ Built-in rule handlers cover all rule types
7. ✅ Rule engine integrated with QC service
8. ✅ Unit tests pass with > 80% coverage
9. ✅ Documentation updated

---

## 🔗 Related Documents

- [Phase 1: Core Architecture](../phase-01-overview.md)
- [Phase 2: CVAT Integration & Workflow Automation](../phase-02-cvat-integration.md)
- [Phase 3: Dashboard UI Development](../phase-03-overview.md)
- [Phase 5: Testing, Optimization & Deployment](../phase-05-testing-deployment.md)
- [Main Development Plan](../README.md)

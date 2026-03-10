"""API routers for all endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, User, UserWorktree, Task, Spec, SecurityProfile
from app.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    UserCreate, UserResponse,
    WorktreeCreate, WorktreeResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    SpecCreate, SpecResponse,
    GitFileStatus, GitCommitRequest, GitStageRequest, GitPullRequest, GitLogEntry,
)
from app.services.git import GitService, WorktreeManager
from app.agents.security.profiles import DEFAULT_PROFILES


# ══════════════════════════════════════════════
#  Projects
# ══════════════════════════════════════════════
projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@projects_router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**body.model_dump())
    db.add(project)
    db.flush()

    # Auto-create security profile based on stack
    stack = body.project_stack or "python"
    profile_data = DEFAULT_PROFILES.get(stack, DEFAULT_PROFILES["python"])
    security_profile = SecurityProfile(
        project_id=project.id,
        stack_type=stack,
        allowed_commands=profile_data["allowed_commands"],
        blocked_commands=profile_data["blocked_commands"],
        allowed_paths=profile_data.get("allowed_path_patterns"),
        blocked_paths=profile_data.get("blocked_path_patterns"),
    )
    db.add(security_profile)
    db.commit()
    db.refresh(project)
    return project


@projects_router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@projects_router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, body: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@projects_router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()


# ══════════════════════════════════════════════
#  Users
# ══════════════════════════════════════════════
users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.username).all()


@users_router.post("", response_model=UserResponse, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(**body.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@users_router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ══════════════════════════════════════════════
#  Worktrees
# ══════════════════════════════════════════════
worktrees_router = APIRouter(prefix="/worktrees", tags=["worktrees"])


@worktrees_router.get("", response_model=list[WorktreeResponse])
def list_worktrees(
    project_id: str = Query(None),
    user_id: str = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(UserWorktree)
    if project_id:
        q = q.filter(UserWorktree.project_id == project_id)
    if user_id:
        q = q.filter(UserWorktree.user_id == user_id)
    return q.all()


@worktrees_router.post("", response_model=WorktreeResponse, status_code=201)
def create_worktree(body: WorktreeCreate, db: Session = Depends(get_db)):
    # Verify user and project exist
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    project = db.query(Project).filter(Project.id == body.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check uniqueness
    existing = (
        db.query(UserWorktree)
        .filter(
            UserWorktree.user_id == body.user_id,
            UserWorktree.project_id == body.project_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Worktree already exists for this user/project")

    # Create worktree in git if repo_url is set
    if project.repo_url:
        mgr = WorktreeManager(project.repo_url)
        mgr.create_worktree(body.user_id, body.branch_name)

    worktree = UserWorktree(**body.model_dump())
    db.add(worktree)
    db.commit()
    db.refresh(worktree)
    return worktree


# ══════════════════════════════════════════════
#  Tasks
# ══════════════════════════════════════════════
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.get("", response_model=list[TaskResponse])
def list_tasks(
    project_id: str = Query(None),
    assigned_user_id: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Task)
    if project_id:
        q = q.filter(Task.project_id == project_id)
    if assigned_user_id:
        q = q.filter(Task.assigned_user_id == assigned_user_id)
    if status:
        q = q.filter(Task.status == status)
    return q.order_by(Task.sort_order, Task.created_at).all()


@tasks_router.post("", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**body.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@tasks_router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@tasks_router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, body: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


@tasks_router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()


# ══════════════════════════════════════════════
#  Specs
# ══════════════════════════════════════════════
specs_router = APIRouter(prefix="/specs", tags=["specs"])


@specs_router.get("", response_model=list[SpecResponse])
def list_specs(project_id: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(Spec)
    if project_id:
        q = q.filter(Spec.project_id == project_id)
    return q.order_by(Spec.created_at.desc()).all()


@specs_router.post("", response_model=SpecResponse, status_code=201)
def create_spec(body: SpecCreate, db: Session = Depends(get_db)):
    spec = Spec(**body.model_dump())
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


# ══════════════════════════════════════════════
#  Git Management
# ══════════════════════════════════════════════
git_router = APIRouter(prefix="/projects/{project_id}/git", tags=["git"])


def _get_git_service(project_id: str, user_id: str, db: Session) -> GitService:
    """Resolve the user's worktree path and create a GitService."""
    worktree = (
        db.query(UserWorktree)
        .filter(
            UserWorktree.project_id == project_id,
            UserWorktree.user_id == user_id,
            UserWorktree.status == "active",
        )
        .first()
    )
    if not worktree:
        raise HTTPException(
            status_code=404,
            detail="No active worktree found for this user/project",
        )
    return GitService(worktree.worktree_path)


@git_router.get("/status", response_model=list[GitFileStatus])
def git_status(
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    return svc.get_status()


@git_router.get("/diff")
def git_diff(
    project_id: str,
    file_path: str = Query(...),
    user_id: str = Query(...),
    staged: bool = Query(False),
    db: Session = Depends(get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    return {"diff": svc.get_diff(file_path, staged=staged)}


@git_router.post("/stage")
def git_stage(
    project_id: str,
    body: GitStageRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    svc.stage_files(body.file_paths)
    return {"message": "Files staged", "files": body.file_paths}


@git_router.post("/commit")
def git_commit(
    project_id: str,
    body: GitCommitRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    commit_hash = svc.commit(body.message)
    return {"message": "Committed", "hash": commit_hash}


@git_router.post("/pull")
def git_pull(
    project_id: str,
    body: GitPullRequest = GitPullRequest(),
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    output = svc.pull(strategy=body.strategy)
    return {"message": "Pull completed", "output": output}


@git_router.post("/push")
def git_push(
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    output = svc.push()
    return {"message": "Push completed", "output": output}


@git_router.get("/log", response_model=list[GitLogEntry])
def git_log(
    project_id: str,
    user_id: str = Query(...),
    count: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    return svc.get_log(count=count)


@git_router.post("/revert")
def git_revert_file(
    project_id: str,
    file_path: str = Query(...),
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    svc.revert_file(file_path)
    return {"message": f"Reverted: {file_path}"}


@git_router.get("/branch")
def git_current_branch(
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    return {"branch": svc.get_current_branch()}

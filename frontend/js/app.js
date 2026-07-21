// API Configuration
const API_BASE = "/api";

// State
let projects = [];
let activeProjectId = null;
let activeProject = null;
let pollInterval = null;

// DOM Elements
const elProjectList = document.getElementById("project-list");
const elNewProjectTitle = document.getElementById("new-project-title");
const elBtnCreateProject = document.getElementById("btn-create-project");

const elWelcomeView = document.getElementById("welcome-view");
const elProjectView = document.getElementById("project-view");

const elActiveProjectTitle = document.getElementById("active-project-title");
const elActiveProjectDate = document.getElementById("active-project-date");
const elActiveProjectStatus = document.getElementById("active-project-status");

const elCfgArtStyle = document.getElementById("cfg-art-style");
const elCfgPresets = document.getElementById("cfg-presets");
const elScenesList = document.getElementById("scenes-list");

const elMergeActionBar = document.getElementById("merge-action-bar");
const elBtnMergeVideo = document.getElementById("btn-merge-video");
const elFinalResultCard = document.getElementById("final-result-card");
const elFinalVideo = document.getElementById("final-video");
const elBtnDownloadVideo = document.getElementById("btn-download-video");

const elMergeProgressWrapper = document.getElementById("merge-progress-wrapper");
const elMergeProgressBar = document.getElementById("merge-progress-bar");
const elMergeProgressStatus = document.getElementById("merge-progress-status");
const elMergeProgressPercent = document.getElementById("merge-progress-percent");

const elToast = document.getElementById("toast");

// Toast helper
function showToast(message, duration = 3000) {
    elToast.innerText = message;
    elToast.classList.remove("hidden");
    setTimeout(() => {
        elToast.classList.add("hidden");
    }, duration);
}

// Format Datetime helper
function formatDate(dateStr) {
    const d = new Date(dateStr);
    return `${d.toLocaleDateString("vi-VN")} ${d.toLocaleTimeString("vi-VN", {hour: '2-digit', minute:'2-digit'})}`;
}

// Fetch Projects List
async function fetchProjects() {
    try {
        const response = await fetch(`${API_BASE}/projects`);
        if (!response.ok) throw new Error("Không thể tải danh sách dự án");
        projects = await response.json();
        renderProjectList();
    } catch (err) {
        showToast(err.message);
    }
}

// Render project items in sidebar
function renderProjectList() {
    if (projects.length === 0) {
        elProjectList.innerHTML = `<div class="loading-text">Chưa có dự án nào. Hãy tạo dự án mới!</div>`;
        return;
    }

    elProjectList.innerHTML = projects.map(p => {
        const isActive = p.id === activeProjectId ? 'active' : '';
        const statusBadge = getStatusBadgeClass(p.status);
        return `
            <div class="project-item ${isActive}" onclick="selectProject(${p.id})">
                <div class="project-item-title">${p.title}</div>
                <div class="project-item-meta">
                    <span>${formatDate(p.created_at)}</span>
                    <span class="badge ${statusBadge}">${translateStatus(p.status)}</span>
                </div>
            </div>
        `;
    }).join("");
}

function getStatusBadgeClass(status) {
    return `badge-${status}`;
}

function translateStatus(status) {
    const mapping = {
        'draft': 'Nháp',
        'generating': 'Đang tạo...',
        'pending_review': 'Đợi duyệt',
        'completed': 'Đã ghép'
    };
    return mapping[status] || status;
}

// Create new project
async function createProject() {
    const title = elNewProjectTitle.value.trim();
    if (!title) {
        showToast("Vui lòng nhập tên câu chuyện!");
        return;
    }

    elBtnCreateProject.disabled = true;
    elBtnCreateProject.innerText = "Đang tạo...";

    try {
        const response = await fetch(`${API_BASE}/projects`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: title })
        });
        
        if (!response.ok) throw new Error("Tạo dự án thất bại");
        const newProject = await response.json();
        
        showToast(`Đã tạo dự án: "${newProject.title}"`);
        elNewProjectTitle.value = "";
        
        await fetchProjects();
        selectProject(newProject.id);
    } catch (err) {
        showToast(err.message);
    } finally {
        elBtnCreateProject.disabled = false;
        elBtnCreateProject.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Tạo Dự Án
        `;
    }
}

// Select a project
function selectProject(projectId) {
    activeProjectId = projectId;
    
    // Đánh dấu active trên sidebar
    const items = elProjectList.querySelectorAll(".project-item");
    items.forEach((item, index) => {
        const p = projects[index];
        if (p && p.id === projectId) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });

    // Hiện view chi tiết với hiệu ứng mượt mà
    elWelcomeView.classList.add("hidden");
    elProjectView.classList.remove("hidden");
    elProjectView.classList.remove("fade-in-up");
    void elProjectView.offsetWidth; // trigger reflow
    elProjectView.classList.add("fade-in-up");

    // Reset view
    elFinalResultCard.classList.add("hidden");
    if (elMergeProgressWrapper) {
        elMergeProgressWrapper.classList.add("hidden");
        elMergeProgressBar.style.width = "0%";
        elMergeProgressPercent.innerText = "0%";
    }

    // Bắt đầu polling thông tin dự án
    startPollingProject();
}

function startPollingProject() {
    if (pollInterval) clearInterval(pollInterval);
    
    fetchProjectDetails();
    pollInterval = setInterval(fetchProjectDetails, 3000);
}

// Fetch Active Project details
async function fetchProjectDetails() {
    if (!activeProjectId) return;

    try {
        const response = await fetch(`${API_BASE}/projects/${activeProjectId}`);
        if (!response.ok) throw new Error("Không thể tải chi tiết dự án");
        activeProject = await response.json();
        
        updateProjectUI();
        
        // Nếu dự án không còn ở trạng thái generating hay các scene đang processing, giảm tần suất/dừng polling
        const anySceneProcessing = activeProject.scenes.some(s => s.status === 'processing' || s.status === 'pending');
        if (activeProject.status !== 'generating' && !anySceneProcessing) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    } catch (err) {
        showToast(err.message);
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

// Update UI details
function updateProjectUI() {
    if (!activeProject) return;

    elActiveProjectTitle.innerText = activeProject.title;
    elActiveProjectDate.innerText = formatDate(activeProject.created_at);
    
    // Status badge
    elActiveProjectStatus.className = `badge ${getStatusBadgeClass(activeProject.status)}`;
    elActiveProjectStatus.innerText = translateStatus(activeProject.status);

    // Art Style config
    elCfgArtStyle.value = activeProject.global_art_style || "";
    
    // Presets
    const presets = JSON.parse(activeProject.character_presets || "{}");
    elCfgPresets.innerHTML = Object.entries(presets).map(([key, val]) => `
        <div class="preset-item">
            <strong>${key}:</strong> ${val}
        </div>
    `).join("");

    // Render Scenes
    renderScenes(activeProject.scenes);

    // Merge bar visibility
    const allScenesSuccess = activeProject.scenes.length > 0 && activeProject.scenes.every(s => s.status === 'success');
    if (allScenesSuccess && activeProject.status !== 'completed') {
        elMergeActionBar.classList.remove("hidden");
    } else {
        elMergeActionBar.classList.add("hidden");
    }

    // Final result
    if (activeProject.status === 'completed') {
        elFinalResultCard.classList.remove("hidden");
        elFinalVideo.src = `/media/output/project_${activeProject.id}_final.mp4`;
        elBtnDownloadVideo.href = elFinalVideo.src;
    } else {
        elFinalResultCard.classList.add("hidden");
    }
}

// Render Scenes Grid
function renderScenes(scenes) {
    elScenesList.innerHTML = scenes.map(s => {
        let mediaContent = "";
        
        if (s.status === 'pending') {
            mediaContent = `
                <div class="spinner"></div>
                <div class="spinner-text">Đang xếp hàng...</div>
            `;
        } else if (s.status === 'processing') {
            mediaContent = `
                <div class="spinner"></div>
                <div class="spinner-text">Đang tạo hình và tiếng...</div>
            `;
        } else if (s.status === 'success') {
            mediaContent = `
                <video src="${s.video_path}" controls></video>
                <audio src="${s.audio_path}" controls></audio>
            `;
        } else {
            mediaContent = `
                <div style="color: var(--danger); font-weight: 600; margin-bottom: 8px;">Tạo asset thất bại</div>
                <button class="btn btn-secondary btn-sm" onclick="triggerRegenerate(${s.id})">Thử lại</button>
            `;
        }

        const focusLabel = s.character_focus !== 'none' ? `<span style="font-size: 11px; padding: 2px 6px; background: rgba(99,102,241,0.2); border-radius: 4px; color: #a5b4fc; font-weight:600;">Focus: ${s.character_focus}</span>` : "";

        return `
            <div class="scene-card card">
                <div class="scene-index">
                    #${s.scene_index}
                </div>
                <div class="scene-info">
                    <div class="narration-box">
                        <label><strong>Lời thoại thuyết minh</strong></label>
                        <p>${s.narration}</p>
                    </div>
                    
                    <div class="prompt-editor-box">
                        <label><strong>Visual Prompt cho AI Video</strong> ${focusLabel}</label>
                        <textarea id="prompt-txt-${s.id}">${s.visual_prompt}</textarea>
                    </div>

                    <div class="scene-actions">
                        <button class="btn btn-primary" onclick="triggerRegenerate(${s.id})">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                            Tạo lại Video
                        </button>
                    </div>
                </div>
                <div class="scene-media">
                    <span class="scene-status-badge status-${s.status}">
                        ${translateSceneStatus(s.status)}
                    </span>
                    ${mediaContent}
                </div>
            </div>
        `;
    }).join("");
}

function translateSceneStatus(status) {
    const mapping = {
        'pending': 'Đợi',
        'processing': 'Tạo...',
        'success': 'Xong',
        'failed': 'Lỗi'
    };
    return mapping[status] || status;
}

// Regenerate single scene video
async function triggerRegenerate(sceneId) {
    const elPrompt = document.getElementById(`prompt-txt-${sceneId}`);
    if (!elPrompt) return;
    
    const newPrompt = elPrompt.value.trim();
    if (!newPrompt) {
        showToast("Prompt không được để trống!");
        return;
    }

    showToast("Đang yêu cầu sinh lại video phân cảnh...");
    
    try {
        const response = await fetch(`${API_BASE}/scenes/${sceneId}/regenerate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ visual_prompt: newPrompt })
        });
        
        if (!response.ok) throw new Error("Yêu cầu sinh lại thất bại");
        
        // Cập nhật ngay lập tức UI và bắt đầu polling
        startPollingProject();
    } catch (err) {
        showToast(err.message);
    }
}

// Merge Video
async function mergeProjectVideo() {
    if (!activeProjectId) return;
    
    elBtnMergeVideo.disabled = true;
    elBtnMergeVideo.innerText = "Đang hợp nhất...";
    
    // Hiện thanh tiến trình
    elMergeProgressWrapper.classList.remove("hidden");
    elMergeProgressBar.style.width = "0%";
    elMergeProgressPercent.innerText = "0%";
    elMergeProgressStatus.innerText = "Bắt đầu thu thập tài nguyên phân cảnh...";

    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += Math.floor(Math.random() * 5) + 2;
            if (progress > 90) progress = 90;
            
            elMergeProgressBar.style.width = `${progress}%`;
            elMergeProgressPercent.innerText = `${progress}%`;

            if (progress < 25) {
                elMergeProgressStatus.innerText = "Đang chuẩn bị tệp tin video & âm thanh...";
            } else if (progress < 55) {
                elMergeProgressStatus.innerText = "Đang co giãn hình ảnh khớp với thuyết minh...";
            } else if (progress < 75) {
                elMergeProgressStatus.innerText = "Đang ghép nối và kết xuất định dạng MP4 H.264...";
            } else {
                elMergeProgressStatus.innerText = "Đang hoàn thiện đóng gói video...";
            }
        }
    }, 400);

    try {
        const response = await fetch(`${API_BASE}/projects/${activeProjectId}/merge`, {
            method: "POST"
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Không thể ghép video");
        }
        
        const result = await response.json();
        
        // Hoàn thành 100%
        clearInterval(progressInterval);
        elMergeProgressBar.style.width = "100%";
        elMergeProgressPercent.innerText = "100%";
        elMergeProgressStatus.innerText = "Hoàn thành xuất sắc!";
        
        showToast("Hợp nhất video thành công!");
        
        setTimeout(async () => {
            elMergeProgressWrapper.classList.add("hidden");
            // Tải lại dự án để hiển thị kết quả
            await fetchProjectDetails();
        }, 1000);

    } catch (err) {
        clearInterval(progressInterval);
        elMergeProgressWrapper.classList.add("hidden");
        showToast(err.message);
    } finally {
        elBtnMergeVideo.disabled = false;
        elBtnMergeVideo.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
            TIẾN HÀNH HỢP NHẤT VIDEO (MERGE)
        `;
    }
}

// Accordion toggle helper
function toggleConfigPanel() {
    const arrow = document.getElementById("config-arrow");
    const content = document.getElementById("config-content");
    
    if (content.style.display === "none") {
        content.style.display = "block";
        arrow.innerText = "▼";
    } else {
        content.style.display = "none";
        arrow.innerText = "▲";
    }
}

// Event Listeners
elBtnCreateProject.addEventListener("click", createProject);
elNewProjectTitle.addEventListener("keypress", (e) => {
    if (e.key === "Enter") createProject();
});
elBtnMergeVideo.addEventListener("click", mergeProjectVideo);

// Initial Load
fetchProjects();
// Đóng config panel mặc định
setTimeout(() => {
    toggleConfigPanel();
}, 200);

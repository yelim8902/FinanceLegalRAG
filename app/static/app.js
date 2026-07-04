const elements = {
  includeSeen: document.querySelector("#include-seen"),
  includeSeenOption: document.querySelector("#include-seen-option"),
  excludeSeenOption: document.querySelector("#exclude-seen-option"),
  impactFilter: document.querySelector("#impact-filter"),
  periodSelect: document.querySelector("#period-select"),
  searchInput: document.querySelector("#search-input"),
  refreshSummary: document.querySelector("#refresh-summary"),
  runMonitor: document.querySelector("#run-monitor"),
  statusText: document.querySelector("#status-text"),
  statusDot: document.querySelector("#status-dot"),
  analyzedCount: document.querySelector("#analyzed-count"),
  totalCount: document.querySelector("#total-count"),
  resultCount: document.querySelector("#result-count"),
  lastChecked: document.querySelector("#last-checked"),
  sourceName: document.querySelector("#source-name"),
  warningCount: document.querySelector("#warning-count"),
  warningSummary: document.querySelector("#warning-summary"),
  seenCount: document.querySelector("#seen-count"),
  resultsList: document.querySelector("#results-list"),
  warningsList: document.querySelector("#warnings-list"),
  seenList: document.querySelector("#seen-list"),
  detailEmpty: document.querySelector("#detail-empty"),
  detailContent: document.querySelector("#detail-content"),
  detailImpact: document.querySelector("#detail-impact"),
  detailMethod: document.querySelector("#detail-method"),
  detailTitle: document.querySelector("#detail-title"),
  detailDate: document.querySelector("#detail-date"),
  detailDepartments: document.querySelector("#detail-departments"),
  detailSummary: document.querySelector("#detail-summary"),
  detailReason: document.querySelector("#detail-reason"),
  detailActions: document.querySelector("#detail-actions"),
  detailEvidence: document.querySelector("#detail-evidence"),
  detailControls: document.querySelector("#detail-controls"),
  detailLink: document.querySelector("#detail-link"),
  controlsCount: document.querySelector("#controls-count"),
  controlsList: document.querySelector("#controls-list"),
  template: document.querySelector("#result-template"),
};

const formatter = new Intl.DateTimeFormat("ko-KR", {
  dateStyle: "medium",
  timeStyle: "short",
});

const state = {
  summaries: [],
  controls: [],
  seenTitles: new Set(),
  markingSeenKeys: new Set(),
  selectedIndex: -1,
};

function setLoading(isLoading, label = "조회 중") {
  elements.refreshSummary.disabled = isLoading;
  elements.runMonitor.disabled = isLoading;
  elements.statusText.textContent = isLoading ? label : "완료";
  elements.statusDot.className = `status-dot ${isLoading ? "loading" : "done"}`;
}

function setStatus(text, status = "idle") {
  elements.statusText.textContent = text;
  elements.statusDot.className = `status-dot ${status}`;
}

function formatDate(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return formatter.format(date);
}

function normalizeImpact(value) {
  return String(value || "unknown").toLowerCase();
}

function getDepartments(summary) {
  return summary.affected_departments?.length ? summary.affected_departments.join(", ") : "-";
}

function renderList(target, items, emptyText) {
  target.replaceChildren();
  if (!items || items.length === 0) {
    const item = document.createElement("li");
    item.textContent = emptyText;
    target.append(item);
    return;
  }
  items.forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    target.append(item);
  });
}

function documentKey(summary) {
  return summary.detail_url || `${summary.published_date || ""}|${summary.title}`;
}

function getFilteredSummaries() {
  const impact = elements.impactFilter.value;
  const query = elements.searchInput.value.trim().toLowerCase();
  return state.summaries.filter((summary) => {
    const matchesImpact = impact === "all" || normalizeImpact(summary.impact_level) === impact;
    const haystack = [
      summary.title,
      summary.document_summary,
      summary.reason,
      summary.notification_message,
      getDepartments(summary),
      ...(summary.recommended_actions || []),
      ...(summary.evidence || []),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return matchesImpact && (!query || haystack.includes(query));
  });
}

function clearDetail() {
  elements.detailEmpty.hidden = false;
  elements.detailContent.hidden = true;
}

function renderDetail(summary) {
  if (!summary) {
    clearDetail();
    return;
  }

  const impact = summary.impact_level || "UNKNOWN";
  elements.detailEmpty.hidden = true;
  elements.detailContent.hidden = false;
  elements.detailImpact.className = `impact-badge ${normalizeImpact(impact)}`;
  elements.detailImpact.textContent = impact;
  elements.detailMethod.textContent = summary.analysis_method || "analysis";
  elements.detailTitle.textContent = summary.title;
  elements.detailDate.textContent = summary.published_date || "-";
  elements.detailDepartments.textContent = getDepartments(summary);
  elements.detailSummary.textContent =
    summary.document_summary || "문서 요약을 생성할 수 없습니다. 원문 상세를 확인하세요.";
  elements.detailReason.textContent =
    summary.reason || summary.notification_message || "영향 검토 의견이 없습니다.";

  renderList(elements.detailActions, summary.recommended_actions || [], "권고 대응안이 없습니다.");
  elements.detailEvidence.replaceChildren();
  const evidenceItems = summary.evidence?.length ? summary.evidence : ["근거 조문 없음"];
  evidenceItems.forEach((value) => {
    const item = document.createElement("span");
    item.textContent = value;
    elements.detailEvidence.append(item);
  });

  renderMatchedControls(summary.matched_controls || []);
  markDocumentSeen(summary);

  if (summary.detail_url) {
    elements.detailLink.href = summary.detail_url;
    elements.detailLink.hidden = false;
  } else {
    elements.detailLink.hidden = true;
  }
}

function renderSeenList() {
  const titles = Array.from(state.seenTitles);
  elements.seenCount.textContent = titles.length;
  renderList(elements.seenList, titles, "이미 본 문서가 없습니다.");
}

async function markDocumentSeen(summary) {
  if (!summary?.title) {
    return;
  }
  const key = documentKey(summary);
  if (state.markingSeenKeys.has(key)) {
    return;
  }
  state.markingSeenKeys.add(key);
  state.seenTitles.add(summary.title);
  renderSeenList();

  try {
    await fetch("/monitor/seen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: summary.title,
        source: elements.sourceName.textContent || "금융위원회 입법예고/규정변경예고",
        published_date: summary.published_date || null,
        detail_url: summary.detail_url || null,
      }),
    });
  } catch {
    state.markingSeenKeys.delete(key);
  }
}

function renderMatchedControls(matchedControls) {
  elements.detailControls.replaceChildren();
  if (!matchedControls.length) {
    const empty = document.createElement("div");
    empty.className = "control-link-card";
    empty.textContent = "연결된 내부 규정이 없습니다.";
    elements.detailControls.append(empty);
    return;
  }

  matchedControls.forEach((matchedControl) => {
    const control =
      state.controls.find((item) => item.control_id === matchedControl.control_id) || matchedControl;
    const card = document.createElement("div");
    card.className = "control-link-card";
    const title = document.createElement("strong");
    title.textContent = `${matchedControl.control_id} · ${control.title}`;
    const meta = document.createElement("span");
    const keywords = matchedControl.matched_keywords?.length
      ? ` · 매칭 키워드 ${matchedControl.matched_keywords.join(", ")}`
      : "";
    meta.textContent = `${control.department || matchedControl.department}${keywords}`;
    card.append(title, meta);
    elements.detailControls.append(card);
  });
}

function renderControls() {
  elements.controlsList.replaceChildren();
  elements.controlsCount.textContent = state.controls.length;
  if (!state.controls.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "내부 회사 규정을 불러오지 못했습니다.";
    elements.controlsList.append(empty);
    return;
  }

  state.controls.forEach((control) => {
    const card = document.createElement("article");
    card.className = "control-card";
    const title = document.createElement("strong");
    title.textContent = `${control.control_id} · ${control.title}`;
    const owner = document.createElement("small");
    owner.textContent = control.department;
    const description = document.createElement("p");
    description.textContent = control.description;
    card.append(title, owner, description);
    elements.controlsList.append(card);
  });
}

function renderResults() {
  const summaries = getFilteredSummaries();
  elements.resultsList.replaceChildren();
  elements.resultCount.textContent = `${summaries.length}건`;

  if (summaries.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "조건에 맞는 검토 문서가 없습니다.";
    elements.resultsList.append(empty);
    clearDetail();
    return;
  }

  summaries.forEach((summary, index) => {
    const node = elements.template.content.firstElementChild.cloneNode(true);
    const impact = summary.impact_level || "UNKNOWN";
    const impactBadge = node.querySelector(".impact-badge");
    const methodBadge = node.querySelector(".method-badge");
    const title = node.querySelector(".document-cell strong");
    const reason = node.querySelector(".reason-preview");
    const department = node.querySelector(".department-cell");

    impactBadge.textContent = impact;
    impactBadge.classList.add(normalizeImpact(impact));
    methodBadge.textContent = summary.analysis_method || "analysis";
    title.textContent = summary.title;
    reason.textContent = summary.document_summary || summary.reason || "문서 요약 없음";
    department.textContent = getDepartments(summary);

    node.addEventListener("click", () => {
      state.selectedIndex = index;
      renderResults();
      renderDetail(summary);
    });

    if (index === state.selectedIndex) {
      node.classList.add("selected");
    }

    elements.resultsList.append(node);
  });

  const nextSelected = summaries[state.selectedIndex] || summaries[0];
  state.selectedIndex = Math.max(0, summaries.indexOf(nextSelected));
  renderDetail(nextSelected);
}

function toSummaryShape(data) {
  if (Array.isArray(data.summaries)) {
    return data;
  }
  return {
    source: data.source,
    monitored_at: data.monitored_at,
    total_documents: data.total_documents,
    analyzed_documents: data.relevant_documents?.length || 0,
    already_seen_documents: data.already_seen_documents || [],
    warnings: data.warnings || [],
    summaries: (data.relevant_documents || []).map((document) => ({
      title: document.title,
      published_date: document.published_date,
      document_summary: document.document_summary || "",
      impact_level: document.impact_level,
      affected_departments: document.affected_departments || [],
      reason: document.reason,
      recommended_actions: document.recommended_actions || [],
      notification_message: document.notification_message,
      matched_controls: document.matched_controls || [],
      evidence: (document.evidence_chunks || []).map((chunk) =>
        [chunk.article_no, chunk.section_title].filter(Boolean).join(": "),
      ),
      detail_url: document.detail_url,
      analysis_method: document.analysis_method,
    })),
  };
}

function renderDashboard(rawData) {
  const data = toSummaryShape(rawData);
  state.summaries = data.summaries || [];
  state.seenTitles = new Set(data.already_seen_documents || []);
  state.selectedIndex = state.summaries.length ? 0 : -1;
  elements.sourceName.textContent = data.source || "-";
  elements.analyzedCount.textContent = data.analyzed_documents ?? 0;
  elements.totalCount.textContent = data.total_documents ?? 0;
  elements.lastChecked.textContent = formatDate(data.monitored_at);
  elements.warningCount.textContent = data.warnings?.length || 0;
  elements.warningSummary.textContent = `알림 ${data.warnings?.length || 0}`;
  renderResults();
  renderList(elements.warningsList, data.warnings || [], "표시할 알림이 없습니다.");
  renderSeenList();
}

async function requestDashboard(mode) {
  const includeSeen = elements.includeSeen.checked;
  const monthsBack = elements.periodSelect.value;
  const endpoint =
    mode === "run"
      ? `/monitor/run?include_seen=${includeSeen}&months_back=${monthsBack}`
      : `/monitor/summary?include_seen=${includeSeen}&months_back=${monthsBack}`;
  setLoading(true, mode === "run" ? "실행 중" : "불러오는 중");
  try {
    const response = await fetch(endpoint, { method: mode === "run" ? "POST" : "GET" });
    if (!response.ok) {
      throw new Error(`API 요청 실패 (${response.status})`);
    }
    renderDashboard(await response.json());
    setStatus("완료", "done");
  } catch (error) {
    setStatus("오류", "error");
    renderList(elements.warningsList, [error.message], "표시할 알림이 없습니다.");
  } finally {
    elements.refreshSummary.disabled = false;
    elements.runMonitor.disabled = false;
  }
}

async function requestControls() {
  try {
    const response = await fetch("/company/controls");
    if (!response.ok) {
      throw new Error("내부 회사 규정 조회 실패");
    }
    state.controls = await response.json();
    renderControls();
  } catch {
    state.controls = [];
    renderControls();
  }
}

function setSeenMode(includeSeen) {
  elements.includeSeen.checked = includeSeen;
  elements.includeSeenOption.classList.toggle("selected", includeSeen);
  elements.excludeSeenOption.classList.toggle("selected", !includeSeen);
  requestDashboard("summary");
}

elements.refreshSummary.addEventListener("click", () => requestDashboard("summary"));
elements.runMonitor.addEventListener("click", () => requestDashboard("run"));
elements.includeSeenOption.addEventListener("click", () => setSeenMode(true));
elements.excludeSeenOption.addEventListener("click", () => setSeenMode(false));
elements.impactFilter.addEventListener("change", () => {
  state.selectedIndex = 0;
  renderResults();
});
elements.periodSelect.addEventListener("change", () => requestDashboard("summary"));
elements.searchInput.addEventListener("input", () => {
  state.selectedIndex = 0;
  renderResults();
});
document.querySelectorAll(".side-panel-toggle").forEach((button) => {
  button.addEventListener("click", () => {
    const panel = button.closest(".side-panel");
    const isCollapsed = panel.classList.toggle("collapsed");
    button.setAttribute("aria-expanded", String(!isCollapsed));
  });
});

requestControls();
requestDashboard("summary");

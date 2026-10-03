import { useState } from "react";
import "./App.css";
import Login from "./Login";

const faqs = [
  {
    question: "What is ReqTrace AI?",
    answer:
      "ReqTrace AI is an AI-powered software requirements analysis system that extracts, organizes, compares, and traces requirements from SRS documents.",
  },
  {
    question: "What type of documents can I upload?",
    answer:
      "ReqTrace AI supports PDF-based Software Requirement Specification (SRS) documents for automated requirement analysis.",
  },
  {
    question: "How does ReqTrace AI identify requirements?",
    answer:
      "The system processes the uploaded SRS document, extracts its text, and uses AI/NLP techniques to identify and structure software requirements for further analysis.",
  },
  {
    question: "Can ReqTrace AI detect changes between SRS versions?",
    answer:
      "Yes. ReqTrace AI compares different versions of SRS documents and identifies added, deleted, and modified requirements.",
  },
  {
    question: "How does the Knowledge Graph help?",
    answer:
      "The Knowledge Graph represents requirements and their relationships, enabling traceability and helping identify potentially affected components when requirements change.",
  },
];

function App() {
  const [openFAQ, setOpenFAQ] = useState(null);
  const [toast, setToast] = useState("");
  const [page, setPage] = useState("home");
  const [authMode, setAuthMode] = useState("login");
  const [dashboardModule, setDashboardModule] = useState("menu");

  // =========================================================
  // SINGLE SRS ANALYSIS
  // =========================================================

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [analysisResult, setAnalysisResult] = useState(null);

  // =========================================================
  // KNOWLEDGE GRAPH
  // =========================================================

  const [graphData, setGraphData] = useState({
    nodes: [],
    edges: [],
  });

  const [selectedGraphNode, setSelectedGraphNode] = useState(null);
  const [graphZoom, setGraphZoom] = useState(1);

  // =========================================================
  // VERSION COMPARISON
  // =========================================================

  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [compareError, setCompareError] = useState("");
  const [compareResult, setCompareResult] = useState(null);

  // =========================================================
  // RELATIONSHIP REVIEW
  // =========================================================

  const [relationshipUpdating, setRelationshipUpdating] = useState(null);
  const [relationshipReviewError, setRelationshipReviewError] = useState("");
  const [relationshipFilter, setRelationshipFilter] = useState("PENDING");

  // =========================================================
  // FAQ
  // =========================================================

  const toggleFAQ = (index) => {
    setOpenFAQ(openFAQ === index ? null : index);
  };
  const showToast = (message) => {
  setToast(message);

  setTimeout(() => {
    setToast("");
  }, 2500);
};

  // =========================================================
// NAVIGATION
// =========================================================

const openDashboard = () => {
  setPage("dashboard");
  setDashboardModule("menu");
  window.scrollTo(0, 0);
};

const logout = () => {
  localStorage.removeItem("reqtrace_token");
  localStorage.removeItem("reqtrace_user");

  setPage("home");
  setDashboardModule("menu");

  window.scrollTo(0, 0);
};

const goHome = () => {
  setPage("home");
  setDashboardModule("menu");
  window.scrollTo(0, 0);
};

const openModule = (module) => {
  setDashboardModule(module);
  window.scrollTo(0, 0);
};

const backToModules = () => {
  setDashboardModule("menu");
  window.scrollTo(0, 0);
};
  // =========================================================
  // UPLOAD SRS
  // =========================================================

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    setUploadError("");
    setAnalysisResult(null);
    setGraphData({
      nodes: [],
      edges: [],
    });
    setSelectedGraphNode(null);
    setGraphZoom(1);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (file.type !== "application/pdf") {
      setSelectedFile(null);
      setUploadError("Please select a PDF SRS document.");
      return;
    }

    setSelectedFile(file);
  };

  const uploadSRS = async () => {
    if (!selectedFile) {
      setUploadError("Please select an SRS PDF first.");
      return;
    }

    setUploading(true);
    setUploadError("");
    setAnalysisResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      if (data.message && !data.requirements) {
        throw new Error(data.message);
      }

      setAnalysisResult(data);

      // Save graph returned by FastAPI
      if (data.graph) {
        setGraphData(data.graph);
      }
    } catch (error) {
      setUploadError(
        "Unable to connect to the ReqTrace AI backend. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setUploading(false);
    }
  };

  // =========================================================
  // OLD SRS
  // =========================================================

  const handleOldFileChange = (event) => {
    const file = event.target.files[0];

    setCompareError("");
    setCompareResult(null);

    if (!file) {
      setOldFile(null);
      return;
    }

    if (file.type !== "application/pdf") {
      setOldFile(null);
      setCompareError(
        "Please select a PDF file for the old SRS version."
      );
      return;
    }

    setOldFile(file);
  };

  // =========================================================
  // NEW SRS
  // =========================================================

  const handleNewFileChange = (event) => {
    const file = event.target.files[0];

    setCompareError("");
    setCompareResult(null);

    if (!file) {
      setNewFile(null);
      return;
    }

    if (file.type !== "application/pdf") {
      setNewFile(null);
      setCompareError(
        "Please select a PDF file for the new SRS version."
      );
      return;
    }

    setNewFile(file);
  };

  // =========================================================
  // COMPARE
  // =========================================================

  const compareVersions = async () => {
    if (!oldFile || !newFile) {
      setCompareError(
        "Please select both old and new SRS documents."
      );
      return;
    }

    setComparing(true);
    setCompareError("");
    setCompareResult(null);

    const formData = new FormData();

    formData.append("old_file", oldFile);
    formData.append("new_file", newFile);

    try {
      const response = await fetch(
  "http://127.0.0.1:8000/compare",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
  const errorData = await response.json();

  const message =
    typeof errorData.detail === "string"
      ? errorData.detail
      : errorData.detail?.message ||
        "Cannot compare these documents.";

  throw new Error(message);
}

const data = await response.json();

      // Initialize the detected relationships for human review.
      // The backend review endpoint changes their initial status to PENDING.
      let reviewedRelationships = data.relationships || [];

      if (reviewedRelationships.length > 0) {
        try {
          const reviewResponse = await fetch(
            "http://localhost:8000/relationships/review",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                relationships: reviewedRelationships,
              }),
            }
          );

          if (reviewResponse.ok) {
            const reviewData = await reviewResponse.json();

            reviewedRelationships =
              reviewData.relationships ||
              reviewedRelationships;
          }
        } catch (reviewError) {
          console.warn(
            "Relationship review initialization failed:",
            reviewError
          );
        }
      }

      data.relationships = reviewedRelationships;

      // Keep the latest V2 graph available to the Knowledge Graph module.
      if (data.graph) {
        data.graph = {
          ...data.graph,
          edges: (data.graph.edges || []).map((edge) => {
            const relationship = reviewedRelationships.find(
              (item) =>
                item.source === edge.source &&
                item.target === edge.target &&
                edge.relation === "RELATED_TO"
            );

            return relationship
              ? {
                  ...edge,
                  status:
                    relationship.status ||
                    edge.status ||
                    "PENDING",
                  confidence:
                    relationship.confidence ??
                    edge.confidence,
                  evidence:
                    relationship.evidence ||
                    edge.evidence,
                }
              : edge;
          }),
        };

        setGraphData(data.graph);
      }

      setCompareResult(data);
      setRelationshipReviewError("");
    } catch (error) {
      setCompareError(
        "Unable to compare the documents. " + "Please upload the correct SRS files for comparison."
      );
    } finally {
      setComparing(false);
    }
  };

  // =========================================================
  // RELATIONSHIP STATUS UPDATE
  // =========================================================

  const updateRelationshipStatus = async (
    relationship,
    status
  ) => {
    if (!relationship?.source || !relationship?.target) {
      return;
    }

    const key =
      `${relationship.source}-${relationship.target}`;

    setRelationshipUpdating(key);
    setRelationshipReviewError("");

    try {
      const response = await fetch(
        "http://localhost:8000/relationships/status",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
         body: JSON.stringify({
  relationships: compareResult?.relationships || [],
  source: relationship.source,
  target: relationship.target,
  status: status,
}),
        }
      );

      if (!response.ok) {
        throw new Error(
          "Unable to update relationship status."
        );
      }

      const data = await response.json();

      const updatedRelationships =
        data.relationships ||
        (compareResult?.relationships || []).map(
          (item) =>
            item.source === relationship.source &&
            item.target === relationship.target
              ? {
                  ...item,
                  status,
                }
              : item
        );

      setCompareResult((current) => {
        if (!current) {
          return current;
        }

        const relationships =
          updatedRelationships ||
          current.relationships ||
          [];

        const graph = current.graph
          ? {
              ...current.graph,
              edges: (current.graph.edges || []).map(
                (edge) => {
                  const updated = relationships.find(
                    (item) =>
                      item.source === edge.source &&
                      item.target === edge.target &&
                      edge.relation === "RELATED_TO"
                  );

                  return updated
                    ? {
                        ...edge,
                        status:
                          updated.status ||
                          edge.status,
                        confidence:
                          updated.confidence ??
                          edge.confidence,
                        evidence:
                          updated.evidence ||
                          edge.evidence,
                      }
                    : edge;
                }
              ),
            }
          : current.graph;

        return {
          ...current,
          relationships,
          graph,
        };
      });

      // Keep the Knowledge Graph module synchronized.
      if (compareResult?.graph) {
        setGraphData({
          ...compareResult.graph,
          edges: (compareResult.graph.edges || []).map(
            (edge) => {
              const updated = updatedRelationships.find(
                (item) =>
                  item.source === edge.source &&
                  item.target === edge.target &&
                  edge.relation === "RELATED_TO"
              );

              return updated
                ? {
                    ...edge,
                    status:
                      updated.status ||
                      edge.status,
                    confidence:
                      updated.confidence ??
                      edge.confidence,
                    evidence:
                      updated.evidence ||
                      edge.evidence,
                  }
                : edge;
            }
          ),
        });
      }
    } catch (error) {
      setRelationshipReviewError(
        "Unable to update the relationship. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setRelationshipUpdating(null);
    }
  };

  // =========================================================
  // DASHBOARD
  // =========================================================

  if (page === "dashboard") {
    const requirementCount =
      analysisResult?.total_requirements ??
      analysisResult?.requirements?.length ??
      0;

    const addedCount = compareResult?.added?.length ?? 0;
    const deletedCount = compareResult?.deleted?.length ?? 0;
    const modifiedCount =
      compareResult?.modified?.length ?? 0;

    // =======================================================
    // DASHBOARD MENU
    // =======================================================

    if (dashboardModule === "menu") {
      return (
        <div className="dashboard-page">

          <header className="dashboard-header">

            <button
              className="dashboard-logo"
              onClick={goHome}
            >
              <span className="dashboard-logo-box">
                R
              </span>

              <span className="dashboard-logo-text">
                REQTRACE <span>AI</span>
              </span>
            </button>

            <nav className="dashboard-nav">

              <button className="dashboard-nav-active">
                DASHBOARD
              </button>

              <button onClick={goHome}>
                HOME
              </button>

              <button onClick={goHome}>
                SIGN OUT
              </button>

            </nav>

          </header>

          <main className="dashboard-main">

            <section className="dashboard-intro">

              <div>

                <div className="dashboard-eyebrow">
                  REQUIREMENT INTELLIGENCE
                </div>

                <h1>
                  Analyze.
                  <br />
                  <span>Compare.</span>
                  <br />
                  Trace.
                </h1>

                <p>
                  Choose a requirement analysis module
                  to continue with your SRS documents.
                </p>

              </div>

              <button
                className="back-home-button"
                onClick={goHome}
              >
                ← BACK TO HOME
              </button>

            </section>

            <section className="dashboard-stats">

              <div className="stat-card">
                <span className="stat-number">
                  01
                </span>

                <span className="stat-label">
                  DOCUMENTS
                </span>

                <strong>
                  {analysisResult ? "03" : "00"}
                </strong>

                <small>
                  SRS DOCUMENTS
                </small>
              </div>

              <div className="stat-card">
                <span className="stat-number">
                  02
                </span>

                <span className="stat-label">
                  REQUIREMENTS
                </span>

                <strong>
                  {String(requirementCount).padStart(
                    2,
                    "0"
                  )}
                </strong>

                <small>
                  EXTRACTED
                </small>
              </div>

              <div className="stat-card">
                <span className="stat-number">
                  03
                </span>

                <span className="stat-label">
                  CHANGES
                </span>

                <strong>
                  {compareResult
                    ? String(
                        addedCount +
                          deletedCount +
                          modifiedCount
                      ).padStart(2, "0")
                    : "—"}
                </strong>

                <small>
                  VERSION ANALYSIS
                </small>
              </div>

              <div className="stat-card">
                <span className="stat-number">
                  04
                </span>

                <span className="stat-label">
                  GRAPH
                </span>

                <strong>
  {graphData.nodes.filter(
    (node) => node.node_type === "requirement"
  ).length
    ? String(
        graphData.nodes.filter(
          (node) => node.node_type === "requirement"
        ).length
      ).padStart(2, "0")
    : "—"}
</strong>

                <small>
                  GRAPH NODES
                </small>
              </div>

            </section>

            {/* MODULES */}

            <section className="future-section">

              <button
                className="future-card"
                onClick={() =>
                  openModule("upload")
                }
              >

                <span>01</span>

                <div>

                  <small>
                    DOCUMENT PROCESSING
                  </small>

                  <h3>
                    Upload SRS
                  </h3>

                  <p>
                    Upload and analyze a single
                    Software Requirement
                    Specification.
                  </p>

                </div>

                <strong>
                  →
                </strong>

              </button>

              <button
                className="future-card"
                onClick={() =>
                  openModule("compare")
                }
              >

                <span>02</span>

                <div>

                  <small>
                    VERSION ANALYSIS
                  </small>

                  <h3>
                    Compare SRS
                  </h3>

                  <p>
                    Compare two SRS versions and
                    detect requirement changes.
                  </p>

                </div>

                <strong>
                  →
                </strong>

              </button>

              <button
                className="future-card"
                onClick={() =>
                  openModule("graph")
                }
              >

                <span>03</span>

                <div>

                  <small>
                    KNOWLEDGE GRAPH
                  </small>

                  <h3>
                    Knowledge Graph
                  </h3>

                  <p>
                    Visualize requirements and
                    their relationships.
                  </p>

                </div>

                <strong>
                  →
                </strong>

              </button>

              <button
                className="future-card"
                onClick={() =>
                  openModule("impact")
                }
              >

                <span>04</span>

                <div>

                  <small>
                    TRACEABILITY
                  </small>

                  <h3>
                    Impact Analysis
                  </h3>

                  <p>
                    Identify potentially affected
                    components when requirements
                    change.
                  </p>

                </div>

                <strong>
                  →
                </strong>

              </button>

            </section>

          </main>

          <footer className="dashboard-footer">

            <div>
              REQTRACE <span>AI</span>
            </div>

            <p>
              AI-BASED SOFTWARE REQUIREMENT ANALYSIS
            </p>

          </footer>

        </div>
      );
    }

    // =======================================================
    // UPLOAD MODULE
    // =======================================================

    if (dashboardModule === "upload") {
      return (
        <div className="dashboard-page">

          <header className="dashboard-header">

            <button
              className="dashboard-logo"
              onClick={backToModules}
            >
              <span className="dashboard-logo-box">
                R
              </span>

              <span className="dashboard-logo-text">
                REQTRACE <span>AI</span>
              </span>
            </button>

            <nav className="dashboard-nav">

              <button onClick={backToModules}>
                DASHBOARD
              </button>

              <button onClick={logout}>
  SIGN OUT
</button>

            </nav>

          </header>

          <main className="dashboard-main">

            <button
              className="back-home-button"
              onClick={backToModules}
            >
              ← BACK TO MODULES
            </button>

            <section className="dashboard-intro">

              <div>

                <div className="dashboard-eyebrow">
                  DOCUMENT PROCESSING
                </div>

                <h1>
                  Upload your
                  <br />
                  <span>SRS.</span>
                </h1>

                <p>
                  Upload a Software Requirement
                  Specification for requirement
                  analysis.
                </p>

              </div>

            </section>

            <section className="upload-section">

              <div className="upload-card">

                <div className="upload-icon">
                  ↑
                </div>

                <h3>
                  Upload SRS Document
                </h3>

                <p>
                  Select a PDF-based Software
                  Requirement Specification
                  for analysis.
                </p>

                <label className="file-select">

                  <input
                    type="file"
                    accept=".pdf,application/pdf"
                    onChange={handleFileChange}
                  />

                  <span>
                    + SELECT PDF
                  </span>

                </label>

                {selectedFile && (
                  <div className="selected-file">

                    <span>PDF</span>

                    <div>

                      <strong>
                        {selectedFile.name}
                      </strong>

                      <small>
                        {(
                          selectedFile.size /
                          1024 /
                          1024
                        ).toFixed(2)}{" "}
                        MB
                      </small>

                    </div>

                  </div>
                )}

                {uploadError && (
                  <div className="upload-error">
                    {uploadError}
                  </div>
                )}

                <button
                  className="analyze-button"
                  onClick={uploadSRS}
                  disabled={
                    uploading ||
                    !selectedFile
                  }
                >

                  {uploading ? (
                    <>
                      <span className="loading-dot"></span>
                      ANALYZING DOCUMENT...
                    </>
                  ) : (
                    <>
                      ANALYZE SRS
                      <span>→</span>
                    </>
                  )}

                </button>

              </div>

            </section>

            {analysisResult && (
              <section className="results-section">

                <div className="section-heading">

                  <div className="section-index">
                    02
                  </div>

                  <div>

                    <div className="section-label">
                      ANALYSIS RESULT
                    </div>

                    <h2>
                      Extracted
                      <span> Requirements.</span>
                    </h2>

                  </div>

                </div>

                <div className="result-summary">

                  <div>
                    <span>
                      DOCUMENT
                    </span>

                    <strong>
                      {analysisResult.filename}
                    </strong>
                  </div>

                  <div>
                    <span>
                      REQUIREMENTS
                    </span>

                    <strong>
                      {requirementCount}
                    </strong>
                  </div>

                  <div>
                    <span>
                      STATUS
                    </span>

                    <strong className="status-success">
                      ANALYZED
                    </strong>
                  </div>

                </div>

                <div className="requirements-list">

                  {analysisResult.requirements?.length >
                  0 ? (
                    analysisResult.requirements.map(
                      (requirement, index) => (
                        <div
                          className="requirement-row"
                          key={
                            requirement.id ||
                            index
                          }
                        >

                          <span className="requirement-id">
                            {requirement.id ||
                              `REQ-${String(
                                index + 1
                              ).padStart(3, "0")}`}
                          </span>

                          <div className="requirement-content">

                            <span className="requirement-type">
                              {requirement.type ||
                                "REQUIREMENT"}
                            </span>

                            <p>
                              {requirement.text ||
                                "Requirement text unavailable."}
                            </p>

                          </div>

                        </div>
                      )
                    )
                  ) : (
                    <div className="empty-result">
                      No requirements were extracted.
                    </div>
                  )}

                </div>

              </section>
            )}

          </main>

        </div>
      );
    }

    // =======================================================
    // COMPARE MODULE
    // =======================================================

    if (dashboardModule === "compare") {
      return (
        <div className="dashboard-page">

          <header className="dashboard-header">

            <button
              className="dashboard-logo"
              onClick={backToModules}
            >
              <span className="dashboard-logo-box">
                R
              </span>

              <span className="dashboard-logo-text">
                REQTRACE <span>AI</span>
              </span>
            </button>

            <nav className="dashboard-nav">

              <button onClick={backToModules}>
                DASHBOARD
              </button>

              <button onClick={goHome}>
                HOME
              </button>

            </nav>

          </header>

          <main className="dashboard-main">

            <button
              className="back-home-button"
              onClick={backToModules}
            >
              ← BACK TO MODULES
            </button>

            <section className="dashboard-intro">

              <div>

                <div className="dashboard-eyebrow">
                  VERSION ANALYSIS
                </div>

                <h1>
                  Compare.
                  <br />
                  <span>SRS Versions.</span>
                </h1>

                <p>
                  Compare two versions of an SRS
                  and identify added, deleted and
                  modified requirements.
                </p>

              </div>

            </section>

            <section className="upload-section">

              <div className="upload-card">

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "1fr 1fr",
                    gap: "20px",
                    width: "100%",
                    marginBottom: "20px",
                  }}
                >

                  <div>

                    <label
                      style={{
                        display: "block",
                        fontSize: "12px",
                        letterSpacing:
                          "1.5px",
                        fontWeight: "600",
                        marginBottom:
                          "10px",
                      }}
                    >
                      OLD SRS VERSION
                    </label>

                    <label className="file-select">

                      <input
                        type="file"
                        accept=".pdf,application/pdf"
                        onChange={
                          handleOldFileChange
                        }
                      />

                      <span>
                        + SELECT OLD PDF
                      </span>

                    </label>

                    {oldFile && (
                      <div
                        className="selected-file"
                        style={{
                          marginTop: "12px",
                        }}
                      >

                        <span>PDF</span>

                        <div>

                          <strong>
                            {oldFile.name}
                          </strong>

                          <small>
                            {(
                              oldFile.size /
                              1024 /
                              1024
                            ).toFixed(2)}{" "}
                            MB
                          </small>

                        </div>

                      </div>
                    )}

                  </div>

                  <div>

                    <label
                      style={{
                        display: "block",
                        fontSize: "12px",
                        letterSpacing:
                          "1.5px",
                        fontWeight: "600",
                        marginBottom:
                          "10px",
                      }}
                    >
                      NEW SRS VERSION
                    </label>

                    <label className="file-select">

                      <input
                        type="file"
                        accept=".pdf,application/pdf"
                        onChange={
                          handleNewFileChange
                        }
                      />

                      <span>
                        + SELECT NEW PDF
                      </span>

                    </label>

                    {newFile && (
                      <div
                        className="selected-file"
                        style={{
                          marginTop: "12px",
                        }}
                      >

                        <span>PDF</span>

                        <div>

                          <strong>
                            {newFile.name}
                          </strong>

                          <small>
                            {(
                              newFile.size /
                              1024 /
                              1024
                            ).toFixed(2)}{" "}
                            MB
                          </small>

                        </div>

                      </div>
                    )}

                  </div>

                </div>

                {compareError && (
                  <div className="upload-error">
                    {compareError}
                  </div>
                )}

                <button
                  className="analyze-button"
                  onClick={
                    compareVersions
                  }
                  disabled={
                    comparing ||
                    !oldFile ||
                    !newFile
                  }
                >

                  {comparing ? (
                    <>
                      <span className="loading-dot"></span>
                      COMPARING VERSIONS...
                    </>
                  ) : (
                    <>
                      COMPARE VERSIONS
                      <span>→</span>
                    </>
                  )}

                </button>

              </div>

            </section>

            {compareResult && (
              <section className="results-section">

                <div className="section-heading">

                  <div className="section-index">
                    02
                  </div>

                  <div>

                    <div className="section-label">
                      COMPARISON RESULT
                    </div>

                    <h2>
                      Requirement
                      <span> Changes.</span>
                    </h2>

                  </div>

                </div>

               <div
  className="result-summary"
  style={{
    display: "grid",
    gridTemplateColumns:
      "repeat(4, minmax(0, 1fr))",
    gap: "14px",
    marginBottom: "30px",
  }}
>
  <div
    style={{
      padding: "22px",
      border: "1px solid rgba(24,50,74,0.12)",
      borderRadius: "12px",
      background: "#ffffff",
    }}
  >
    <span
      style={{
        display: "block",
        fontSize: "11px",
        fontWeight: "700",
        letterSpacing: "1.5px",
        marginBottom: "8px",
      }}
    >
      ADDED
    </span>

    <strong
      style={{
        display: "block",
        fontSize: "32px",
      }}
    >
      {addedCount}
    </strong>

    <small>
      New requirements
    </small>
  </div>

  <div
    style={{
      padding: "22px",
      border: "1px solid rgba(24,50,74,0.12)",
      borderRadius: "12px",
      background: "#ffffff",
    }}
  >
    <span
      style={{
        display: "block",
        fontSize: "11px",
        fontWeight: "700",
        letterSpacing: "1.5px",
        marginBottom: "8px",
      }}
    >
      DELETED
    </span>

    <strong
      style={{
        display: "block",
        fontSize: "32px",
      }}
    >
      {deletedCount}
    </strong>

    <small>
      Removed requirements
    </small>
  </div>

  <div
    style={{
      padding: "22px",
      border: "1px solid rgba(24,50,74,0.12)",
      borderRadius: "12px",
      background: "#ffffff",
    }}
  >
    <span
      style={{
        display: "block",
        fontSize: "11px",
        fontWeight: "700",
        letterSpacing: "1.5px",
        marginBottom: "8px",
      }}
    >
      MODIFIED
    </span>

    <strong
      style={{
        display: "block",
        fontSize: "32px",
      }}
    >
      {modifiedCount}
    </strong>

    <small>
      Changed requirements
    </small>
  </div>

  <div
    style={{
      padding: "22px",
      border: "1px solid rgba(24,50,74,0.12)",
      borderRadius: "12px",
      background: "#ffffff",
    }}
  >
    <span
      style={{
        display: "block",
        fontSize: "11px",
        fontWeight: "700",
        letterSpacing: "1.5px",
        marginBottom: "8px",
      }}
    >
      RELATIONSHIPS
    </span>

    <strong
      style={{
        display: "block",
        fontSize: "32px",
      }}
    >
      {compareResult.relationships?.length ?? 0}
    </strong>

    <small>
      Detected relationships
    </small>
  </div>
</div>

                <div className="requirements-list">

                  <div
                    style={{
                      padding: "18px 0",
                      borderBottom:
                        "1px solid rgba(24,50,74,0.12)",
                      fontWeight: "600",
                      letterSpacing: "1px",
                    }}
                  >
                    ADDED REQUIREMENTS
                  </div>

                  {addedCount > 0 ? (
                    compareResult.added.map(
                      (item, index) => (
                        <div
                          className="requirement-row"
                          key={`added-${index}`}
                        >

                          <span className="requirement-id">
                            +
                          </span>

                          <div className="requirement-content">

                            <span className="requirement-type">
                              ADDED
                            </span>

                            <p>
                              {item?.text || item}
                            </p>

                          </div>

                        </div>
                      )
                    )
                  ) : (
                    <div className="empty-result">
                      No added requirements.
                    </div>
                  )}

                </div>

                <div
                  className="requirements-list"
                  style={{
                    marginTop: "20px",
                  }}
                >

                  <div
                    style={{
                      padding: "18px 0",
                      borderBottom:
                        "1px solid rgba(24,50,74,0.12)",
                      fontWeight: "600",
                      letterSpacing: "1px",
                    }}
                  >
                    DELETED REQUIREMENTS
                  </div>

                  {deletedCount > 0 ? (
                    compareResult.deleted.map(
                      (item, index) => (
                        <div
                          className="requirement-row"
                          key={`deleted-${index}`}
                        >

                          <span className="requirement-id">
                            −
                          </span>

                          <div className="requirement-content">

                            <span className="requirement-type">
                              DELETED
                            </span>

                            <p>
                              {item?.text || item}
                            </p>

                          </div>

                        </div>
                      )
                    )
                  ) : (
                    <div className="empty-result">
                      No deleted requirements.
                    </div>
                  )}

                </div>

                <div
                  className="requirements-list"
                  style={{
                    marginTop: "20px",
                  }}
                >

                  <div
                    style={{
                      padding: "18px 0",
                      borderBottom:
                        "1px solid rgba(24,50,74,0.12)",
                      fontWeight: "600",
                      letterSpacing: "1px",
                    }}
                  >
                    MODIFIED REQUIREMENTS
                  </div>

                  {modifiedCount > 0 ? (
                    compareResult.modified.map(
                      (item, index) => (
                        <div
                          className="requirement-row"
                          key={`modified-${index}`}
                        >

                          <span className="requirement-id">
                            ~
                          </span>

                          <div className="requirement-content">

                            <span className="requirement-type">
                              MODIFIED
                            </span>

                            <p>
                              <strong>
                                OLD:
                              </strong>{" "}
                              {item.old}
                            </p>

                            <p>
                              <strong>
                                NEW:
                              </strong>{" "}
                              {item.new}
                            </p>

                          </div>

                        </div>
                      )
                    )
                  ) : (
                    <div className="empty-result">
                      No modified requirements.
                    </div>
                  )}

                </div>

                {/* RELATIONSHIP REVIEW */}
                <section
                  className="requirements-list"
                  style={{
                    marginTop: "30px",
                  }}
                >
                  <div
                    style={{
                      padding: "18px 0",
                      borderBottom:
                        "1px solid rgba(24,50,74,0.12)",
                      fontWeight: "600",
                      letterSpacing: "1px",
                    }}
                  >
                    RELATIONSHIP REVIEW
                  </div>

                  {relationshipReviewError && (
                    <div
                      className="upload-error"
                      style={{
                        marginTop: "18px",
                      }}
                    >
                      {relationshipReviewError}
                    </div>
                  )}

                  {(() => {
  const relationships =
    compareResult.relationships || [];

  const autoAcceptedCount =
    relationships.filter(
      (item) =>
        item.status === "AUTO_ACCEPTED"
    ).length;

  const pendingCount =
    relationships.filter(
      (item) =>
        (item.status || "PENDING") ===
        "PENDING"
    ).length;

  const acceptedCount =
    relationships.filter(
      (item) =>
        item.status === "ACCEPTED"
    ).length;

  const rejectedCount =
    relationships.filter(
      (item) =>
        item.status === "REJECTED"
    ).length;

                   return (
  <>
    <div
      style={{
        display: "grid",
        gridTemplateColumns:
          "repeat(5, 1fr)",
        gap: "12px",
        marginTop: "20px",
        marginBottom: "20px",
      }}
    >
      {[
        {
          label: "DETECTED",
          value: relationships.length,
        },
        {
          label: "AUTO-ACCEPTED",
          value: autoAcceptedCount,
        },
        {
          label: "PENDING",
          value: pendingCount,
        },
        {
          label: "ACCEPTED",
          value: acceptedCount,
        },
        {
          label: "REJECTED",
          value: rejectedCount,
        },
      ].map((stat) => (
        <div
          key={stat.label}
          onClick={() =>
  setRelationshipFilter(stat.label)
}
          style={{
            border:
              "1px solid rgba(24,50,74,0.12)",
            padding: "16px",
                        cursor: "pointer",
            background:
              relationshipFilter === stat.label
                ? "rgba(24,50,74,0.08)"
                : "transparent",
          }}
        >
          <div
            style={{
              fontSize: "9px",
              letterSpacing: "1.5px",
              color: "#806F5A",
              marginBottom: "8px",
            }}
          >
            {stat.label}
          </div>

          <strong
            style={{
              fontSize: "24px",
              color: "#18324A",
            }}
          >
            {stat.value}
          </strong>
        </div>
      ))}
    </div>
      {/* RELATIONSHIP LIST */}
    <div
      style={{
        marginTop: "20px",
        maxHeight: "400px",
        overflowY: "auto",
        border: "1px solid rgba(24,50,74,0.12)",
        padding: "12px",
      }}
    >
    {relationships
  .filter((item) => {
    const itemStatus = item.status || "PENDING";

    if (relationshipFilter === "DETECTED") {
      return true;
    }

    if (relationshipFilter === "AUTO-ACCEPTED") {
      return itemStatus === "AUTO_ACCEPTED";
    }

    if (relationshipFilter === "PENDING") {
      return itemStatus === "PENDING";
    }

    if (relationshipFilter === "ACCEPTED") {
      return itemStatus === "ACCEPTED";
    }

    if (relationshipFilter === "REJECTED") {
      return itemStatus === "REJECTED";
    }

    return false;
  })
  .map((item, index) => (
          <div
            key={`${item.source}-${item.target}-${index}`}
            style={{
              padding: "14px",
              marginBottom: "10px",
              border: "1px solid rgba(24,50,74,0.12)",
            }}
          >
            <strong>
              {item.source} → {item.target}
            </strong>

            <div style={{ marginTop: "6px" }}>
              {item.relation || "RELATED_TO"}
            </div>

            <div style={{ marginTop: "6px" }}>
              Confidence: {item.confidence ?? 0}
            </div>

            {item.evidence && (
              <div style={{ marginTop: "6px" }}>
                {item.evidence}
              </div>
            )}

            {(item.status || "PENDING") === "PENDING" && (
              <div
                style={{
                  marginTop: "12px",
                  display: "flex",
                  gap: "8px",
                }}
              >
                <button
                  type="button"
                  onClick={() =>
                   updateRelationshipAction(
                      item,
                      "ACCEPTED"
                    )
                  }
                >
                  ACCEPT
                </button>

                <button
                  type="button"
                  onClick={() =>
                    updateRelationshipAction(
                      item,
                      "REJECTED"
                    )
                  }
                >
                  REJECT
                </button>
              </div>
            )}
          </div>
        ))}
    </div>

    {relationships.length > 0 ? (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "14px",
        }}
      >
        {relationships .filter((relationship) => {
    const status = relationship.status || "PENDING";

    if (relationshipFilter === "DETECTED") {
      return true;
    }

    if (relationshipFilter === "AUTO-ACCEPTED") {
      return status === "AUTO_ACCEPTED";
    }

    if (relationshipFilter === "PENDING") {
      return status === "PENDING";
    }

    if (relationshipFilter === "ACCEPTED") {
      return status === "ACCEPTED";
    }

    if (relationshipFilter === "REJECTED") {
      return status === "REJECTED";
    }

    return false;
  }).map(
          (relationship, index) => {
            const status =
              relationship.status ||
              "PENDING";
                                const key =
                                  `${relationship.source}-${relationship.target}`;

                                const isUpdating =
                                  relationshipUpdating ===
                                  key;

                                const confidence =
                                  Number(
                                    relationship.confidence ??
                                      relationship.similarity ??
                                      0
                                  );

                                return (
                                  <div
                                    key={`${key}-${index}`}
                                    style={{
                                      border:
                                        "1px solid rgba(24,50,74,0.14)",
                                      padding: "20px",
                                      background:
                                        "#FFFDF8",
                                    }}
                                  >
                                    <div
                                      style={{
                                        display: "flex",
                                        justifyContent:
                                          "space-between",
                                        alignItems:
                                          "center",
                                        gap: "15px",
                                        flexWrap: "wrap",
                                      }}
                                    >
                                      <div
                                        style={{
                                          display: "flex",
                                          alignItems:
                                            "center",
                                          gap: "10px",
                                          flexWrap: "wrap",
                                        }}
                                      >
                                        <span
                                          style={{
                                            fontWeight: "700",
                                            color: "#18324A",
                                          }}
                                        >
                                          {relationship.source}
                                        </span>

                                        <span
                                          style={{
                                            color: "#806F5A",
                                            fontSize: "12px",
                                            letterSpacing:
                                              "1px",
                                          }}
                                        >
                                          →
                                        </span>

                                        <span
                                          style={{
                                            fontWeight: "700",
                                            color: "#18324A",
                                          }}
                                        >
                                          {relationship.target}
                                        </span>

                                        <span
                                          style={{
                                            border:
                                              "1px solid #2F6B9A",
                                            color: "#2F6B9A",
                                            padding:
                                              "5px 8px",
                                            fontSize: "9px",
                                            letterSpacing:
                                              "1px",
                                          }}
                                        >
                                          RELATED_TO
                                        </span>
                                      </div>

                                      <span
                                        style={{
                                          padding:
                                            "6px 10px",
                                          fontSize: "10px",
                                          letterSpacing:
                                            "1.3px",
                                          fontWeight: "700",
                                          border:
                                            status ===
                                            "ACCEPTED"
                                              ? "1px solid #477A5A"
                                              : status ===
                                                "REJECTED"
                                              ? "1px solid #9A5555"
                                              : "1px solid #8A6A3D",
                                          color:
                                            status ===
                                            "ACCEPTED"
                                              ? "#477A5A"
                                              : status ===
                                                "REJECTED"
                                              ? "#9A5555"
                                              : "#8A6A3D",
                                        }}
                                      >
                                        {status}
                                      </span>
                                    </div>

                                    <div
                                      style={{
                                        marginTop: "16px",
                                        display: "grid",
                                        gridTemplateColumns:
                                          "180px 1fr",
                                        gap: "20px",
                                      }}
                                    >
                                      <div>
                                        <div
                                          style={{
                                            fontSize: "9px",
                                            letterSpacing:
                                              "1.5px",
                                            color: "#806F5A",
                                            marginBottom:
                                              "7px",
                                          }}
                                        >
                                          CONFIDENCE
                                        </div>

                                        <strong
                                          style={{
                                            fontSize: "20px",
                                            color: "#18324A",
                                          }}
                                        >
                                          {(
                                            confidence *
                                            100
                                          ).toFixed(0)}
                                          %
                                        </strong>
                                      </div>

                                      <div>
                                        <div
                                          style={{
                                            fontSize: "9px",
                                            letterSpacing:
                                              "1.5px",
                                            color: "#806F5A",
                                            marginBottom:
                                              "7px",
                                          }}
                                        >
                                          EVIDENCE
                                        </div>

                                        <p
                                          style={{
                                            margin: 0,
                                            lineHeight:
                                              "1.6",
                                            color:
                                              "#52708B",
                                            fontSize:
                                              "13px",
                                          }}
                                        >
                                          {relationship.evidence ||
                                            "No evidence provided."}
                                        </p>
                                      </div>
                                    </div>

                                    <div
                                      style={{
                                        display: "flex",
                                        justifyContent:
                                          "flex-end",
                                        gap: "10px",
                                        marginTop: "18px",
                                      }}
                                    >
                                      <button
                                        type="button"
                                        onClick={() =>
                                          updateRelationshipStatus(
                                            relationship,
                                            "ACCEPTED"
                                          )
                                        }
                                       disabled={
  isUpdating }
                                        style={{
                                          border:
                                            "1px solid #477A5A",
                                          background:
                                            status ===
                                            "ACCEPTED"
                                              ? "#477A5A"
                                              : "transparent",
                                          color:
                                            status ===
                                            "ACCEPTED"
                                              ? "#FFFFFF"
                                              : "#477A5A",
                                          padding:
                                            "9px 14px",
                                          fontSize: "10px",
                                          letterSpacing:
                                            "1.2px",
                                          fontWeight:
                                            "700",
                                          cursor:
                                            isUpdating ||
                                            status ===
                                              "ACCEPTED"
                                              ? "default"
                                              : "pointer",
                                          opacity:
                                            isUpdating
                                              ? 0.55
                                              : 1,
                                        }}
                                      >
                                        {isUpdating &&
                                        status !==
                                          "ACCEPTED"
                                          ? "UPDATING..."
                                          : "ACCEPT"}
                                      </button>

                                      <button
                                        type="button"
                                        onClick={() =>
                                          updateRelationshipStatus(
                                            relationship,
                                            "REJECTED"
                                          )
                                        }
                                       disabled={
  isUpdating 
}
                                        style={{
                                          border:
                                            "1px solid #9A5555",
                                          background:
                                            status ===
                                            "REJECTED"
                                              ? "#9A5555"
                                              : "transparent",
                                          color:
                                            status ===
                                            "REJECTED"
                                              ? "#FFFFFF"
                                              : "#9A5555",
                                          padding:
                                            "9px 14px",
                                          fontSize: "10px",
                                          letterSpacing:
                                            "1.2px",
                                          fontWeight:
                                            "700",
                                          cursor:
                                            isUpdating ||
                                            status ===
                                              "REJECTED"
                                              ? "default"
                                              : "pointer",
                                          opacity:
                                            isUpdating
                                              ? 0.55
                                              : 1,
                                        }}
                                      >
                                       {status === "AUTO_ACCEPTED"
  ? "AUTO-ACCEPTED"
  : isUpdating && status !== "REJECTED"
    ? "UPDATING..."
    : "REJECT"}
                                      </button>
                                    </div>
                                  </div>
                                );
                              }
                            )}
                          </div>
                        ) : (
                          <div className="empty-result">
                            No relationships were detected.
                          </div>
                        )}
                      </>
                    );
                  })()}
                </section>

                {/* TRACEABILITY */}
                <section
                  className="requirements-list"
                  style={{
                    marginTop: "30px",
                  }}
                >
                  <div
                    style={{
                      padding: "18px 0",
                      borderBottom:
                        "1px solid rgba(24,50,74,0.12)",
                      fontWeight: "600",
                      letterSpacing: "1px",
                    }}
                  >
                    TRACEABILITY & IMPACT
                  </div>

                  {compareResult.traceability?.length > 0 ? (
                    compareResult.traceability.map(
                      (item, index) => (
                        <div
                          className="requirement-row"
                          key={`trace-${item.requirement_id}-${index}`}
                          style={{
                            display: "block",
                            padding: "24px 0",
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              gap: "20px",
                              flexWrap: "wrap",
                              marginBottom: "16px",
                            }}
                          >
                            <div>
                              <span className="requirement-id">
                                {item.requirement_id}
                              </span>
                              <span
                                className="requirement-type"
                                style={{ marginLeft: "20px" }}
                              >
                                {item.change_type || "MODIFIED"}
                              </span>
                            </div>
                            <span
                              style={{
                                fontSize: "11px",
                                letterSpacing: "1.5px",
                                color: "#52708B",
                              }}
                            >
                              TRACEABLE
                            </span>
                          </div>

                          <div
                            style={{
                              display: "grid",
                              gridTemplateColumns: "1fr 1fr",
                              gap: "20px",
                            }}
                          >
                            <div>
                              <div
                                style={{
                                  fontSize: "10px",
                                  letterSpacing: "2px",
                                  color: "#806F5A",
                                  marginBottom: "10px",
                                }}
                              >
                                RELATED REQUIREMENTS
                              </div>

                              {item.related_requirements?.length > 0 ? (
                                <div
                                  style={{
                                    display: "flex",
                                    flexWrap: "wrap",
                                    gap: "8px",
                                  }}
                                >
                                  {[...new Set(item.related_requirements)].map(
                                    (id) => (
                                      <span
                                        key={id}
                                        style={{
                                          border: "1px solid #2F6B9A",
                                          color: "#2F6B9A",
                                          padding: "6px 10px",
                                          fontSize: "12px",
                                        }}
                                      >
                                        {id}
                                      </span>
                                    )
                                  )}
                                </div>
                              ) : (
                                <span
                                  style={{
                                    color: "#8A8A8A",
                                    fontSize: "13px",
                                  }}
                                >
                                  No related requirements.
                                </span>
                              )}
                            </div>

                            <div>
                              <div
                                style={{
                                  fontSize: "10px",
                                  letterSpacing: "2px",
                                  color: "#806F5A",
                                  marginBottom: "10px",
                                }}
                              >
                                AFFECTED COMPONENTS
                              </div>

                              {item.affected_components?.length > 0 ? (
                                <div
                                  style={{
                                    display: "flex",
                                    flexWrap: "wrap",
                                    gap: "8px",
                                  }}
                                >
                                  {[...new Set(item.affected_components)].map(
                                    (id) => (
                                      <span
                                        key={id}
                                        style={{
                                          border: "1px solid #8A6A3D",
                                          color: "#8A6A3D",
                                          padding: "6px 10px",
                                          fontSize: "12px",
                                        }}
                                      >
                                        {id}
                                      </span>
                                    )
                                  )}
                                </div>
                              ) : (
                                <span
                                  style={{
                                    color: "#8A8A8A",
                                    fontSize: "13px",
                                  }}
                                >
                                  No affected components.
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      )
                    )
                  ) : (
                    <div className="empty-result">
                      No traceability data returned.
                    </div>
                  )}
                </section>

                {/* IMPACT SUMMARY */}
                <section
                  className="result-summary"
                  style={{ marginTop: "30px" }}
                >
                  <div>
                    <span>TOTAL CHANGES</span>
                    <strong>
                      {compareResult.impact_summary?.total_changes ??
                        addedCount + deletedCount + modifiedCount}
                    </strong>
                  </div>

                  <div>
                    <span>MODIFIED</span>
                    <strong>
                      {compareResult.impact_summary?.modified ??
                        modifiedCount}
                    </strong>
                  </div>

                  <div>
                    <span>AFFECTED COMPONENTS</span>
                    <strong>
                      {compareResult.impact_summary?.affected_components ?? 0}
                    </strong>
                  </div>

                  <div>
                    <span>STATUS</span>
                    <strong className="status-success">
                      COMPLETE
                    </strong>
                  </div>
                </section>

              </section>
            )}

          </main>

        </div>
      );
    }

    // =======================================================
    // KNOWLEDGE GRAPH MODULE
    // =======================================================

    if (dashboardModule === "graph") {
      const nodes = graphData.nodes || [];
      const edges = graphData.edges || [];

      const requirementNodes = nodes.filter(
        (node) => node.node_type === "requirement"
      );

      const componentNodes = nodes.filter(
        (node) => node.node_type === "component"
      );

      const canvasWidth = 1100;
      const canvasHeight = 680;
      const centerX = canvasWidth / 2;
      const centerY = canvasHeight / 2;

      /*
       * Arrange requirements in the centre and components
       * around them. This keeps the graph readable without
       * adding another frontend dependency.
       */
      const positions = {};

      const requirementRadius =
        Math.min(
          230,
          90 + requirementNodes.length * 24
        );

      requirementNodes.forEach((node, index) => {
        const angle =
          (index / Math.max(requirementNodes.length, 1)) *
            Math.PI *
            2 -
          Math.PI / 2;

        positions[node.id] = {
          x:
            centerX +
            Math.cos(angle) * requirementRadius,
          y:
            centerY +
            Math.sin(angle) * requirementRadius,
        };
      });

      const componentRadius = 290;

      componentNodes.forEach((node, index) => {
        const angle =
          (index / Math.max(componentNodes.length, 1)) *
            Math.PI *
            2 -
          Math.PI / 2;

        positions[node.id] = {
          x:
            centerX +
            Math.cos(angle) * componentRadius,
          y:
            centerY +
            Math.sin(angle) * componentRadius,
        };
      });

      /*
       * If a graph contains an unexpected node type, place it
       * near the centre so its relationships are still visible.
       */
      nodes
        .filter((node) => !positions[node.id])
        .forEach((node, index) => {
          positions[node.id] = {
            x:
              centerX +
              ((index % 3) - 1) * 170,
            y:
              centerY +
              (Math.floor(index / 3) - 1) * 150,
          };
        });

      const nodeWidth = 190;
      const nodeHeight = 86;

      const truncate = (value, max = 28) => {
        if (!value) return "";
        const text = String(value);
        return text.length > max
          ? `${text.slice(0, max)}…`
          : text;
      };

      const selectedNode = nodes.find(
        (node) => node.id === selectedGraphNode
      );

      const selectedEdges = selectedNode
        ? edges.filter(
            (edge) =>
              edge.source === selectedNode.id ||
              edge.target === selectedNode.id
          )
        : [];

      const selectedRelated = selectedNode
        ? selectedEdges
            .filter(
              (edge) =>
                edge.relation === "RELATED_TO"
            )
            .map((edge) =>
              edge.source === selectedNode.id
                ? edge.target
                : edge.source
            )
        : [];

      const selectedComponents = selectedNode
        ? selectedEdges
            .filter(
              (edge) =>
                edge.relation === "AFFECTS"
            )
            .map((edge) =>
              edge.source === selectedNode.id
                ? edge.target
                : edge.source
            )
        : [];

      const getEdgeColor = (relation) =>
        relation === "AFFECTS"
          ? "#8A6A3D"
          : "#2F6B9A";

      return (
        <div className="dashboard-page">

          <header className="dashboard-header">

            <button
              className="dashboard-logo"
              onClick={backToModules}
            >
              <span className="dashboard-logo-box">
                R
              </span>

              <span className="dashboard-logo-text">
                REQTRACE <span>AI</span>
              </span>
            </button>

            <nav className="dashboard-nav">

              <button onClick={backToModules}>
                DASHBOARD
              </button>

              <button onClick={goHome}>
                HOME
              </button>

            </nav>

          </header>

          <main className="dashboard-main">

            <button
              className="back-home-button"
              onClick={backToModules}
            >
              ← BACK TO MODULES
            </button>

            <section className="dashboard-intro">

              <div>

                <div className="dashboard-eyebrow">
                  KNOWLEDGE GRAPH
                </div>

                <h1>
                  Explore.
                  <br />
                  <span>Relationships.</span>
                </h1>

                <p>
                  Interactive visualization of
                  NLP-derived requirement
                  relationships and affected
                  software components.
                </p>

              </div>

            </section>

            <section className="result-summary">

              <div>
                <span>REQUIREMENTS</span>
                <strong>
                  {requirementNodes.length}
                </strong>
              </div>

              <div>
                <span>COMPONENTS</span>
                <strong>
                  {componentNodes.length}
                </strong>
              </div>

              <div>
                <span>RELATIONSHIPS</span>
                <strong>
                  {edges.length}
                </strong>
              </div>

              <div>
                <span>GRAPH STATUS</span>
                <strong className="status-success">
                  {nodes.length ? "READY" : "EMPTY"}
                </strong>
              </div>

            </section>

            <section
              style={{
                width: "100%",
                maxWidth: "1100px",
                margin: "40px auto 0",
                background: "#FFFDF8",
                border: "1px solid #D5CCBE",
                borderRadius: "4px",
                padding: "20px",
                boxSizing: "border-box",
              }}
            >

              {!nodes.length ? (

                <div
                  style={{
                    minHeight: "420px",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    textAlign: "center",
                    color: "#3D5265",
                  }}
                >

                  <div
                    style={{
                      fontSize: "42px",
                      marginBottom: "15px",
                    }}
                  >
                    ◇
                  </div>

                  <h3
                    style={{
                      color: "#18324A",
                      marginBottom: "8px",
                    }}
                  >
                    No Graph Data
                  </h3>

                  <p>
                    Upload and analyze an SRS
                    document first.
                  </p>

                  <button
                    className="analyze-button"
                    onClick={() =>
                      openModule("upload")
                    }
                    style={{
                      marginTop: "20px",
                    }}
                  >
                    UPLOAD SRS
                    <span>→</span>
                  </button>

                </div>

              ) : (

                <>

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "15px",
                      marginBottom: "15px",
                      flexWrap: "wrap",
                    }}
                  >

                    <div
                      style={{
                        fontSize: "11px",
                        letterSpacing: "1.5px",
                        color: "#52708B",
                      }}
                    >
                      CLICK A NODE TO INSPECT ITS
                      RELATIONSHIPS
                    </div>

                    <div
                      style={{
                        display: "flex",
                        gap: "8px",
                      }}
                    >

                      <button
                        type="button"
                        onClick={() =>
                          setGraphZoom(
                            Math.max(
                              0.7,
                              Number(
                                (
                                  graphZoom - 0.1
                                ).toFixed(1)
                              )
                            )
                          )
                        }
                        style={{
                          width: "38px",
                          height: "34px",
                          border:
                            "1px solid #D5CCBE",
                          background:
                            "#F3ECDF",
                          color: "#18324A",
                          cursor: "pointer",
                          fontSize: "18px",
                        }}
                      >
                        −
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          setGraphZoom(
                            Math.min(
                              1.5,
                              Number(
                                (
                                  graphZoom + 0.1
                                ).toFixed(1)
                              )
                            )
                          )
                        }
                        style={{
                          width: "38px",
                          height: "34px",
                          border:
                            "1px solid #D5CCBE",
                          background:
                            "#F3ECDF",
                          color: "#18324A",
                          cursor: "pointer",
                          fontSize: "18px",
                        }}
                      >
                        +
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setGraphZoom(1);
                          setSelectedGraphNode(null);
                        }}
                        style={{
                          padding: "0 12px",
                          height: "34px",
                          border:
                            "1px solid #D5CCBE",
                          background:
                            "#F3ECDF",
                          color: "#18324A",
                          cursor: "pointer",
                          fontSize: "11px",
                          letterSpacing: "1px",
                        }}
                      >
                        RESET
                      </button>

                    </div>

                  </div>

                  <div
                    style={{
                      width: "100%",
                      overflow: "auto",
                      border:
                        "1px solid rgba(24,50,74,0.08)",
                      background:
                        "linear-gradient(180deg,#fffdf8,#f8f2e8)",
                    }}
                  >

                    <svg
                      width={canvasWidth}
                      height={canvasHeight}
                      viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
                      style={{
                        display: "block",
                        margin: "0 auto",
                        transformOrigin:
                          "center center",
                        transform:
                          `scale(${graphZoom})`,
                        transition:
                          "transform 180ms ease",
                      }}
                    >

                      <defs>

                        <marker
                          id="reqtrace-arrow"
                          viewBox="0 0 10 10"
                          refX="9"
                          refY="5"
                          markerWidth="6"
                          markerHeight="6"
                          orient="auto-start-reverse"
                        >
                          <path
                            d="M 0 0 L 10 5 L 0 10 z"
                            fill="#2F6B9A"
                          />
                        </marker>

                        <marker
                          id="reqtrace-arrow-affects"
                          viewBox="0 0 10 10"
                          refX="9"
                          refY="5"
                          markerWidth="6"
                          markerHeight="6"
                          orient="auto-start-reverse"
                        >
                          <path
                            d="M 0 0 L 10 5 L 0 10 z"
                            fill="#8A6A3D"
                          />
                        </marker>

                      </defs>

                      {/* EDGES */}

                      {edges.map((edge, index) => {

                        const source =
                          positions[edge.source];

                        const target =
                          positions[edge.target];

                        if (!source || !target) {
                          return null;
                        }

                        const dx =
                          target.x - source.x;

                        const dy =
                          target.y - source.y;

                        const length =
                          Math.sqrt(
                            dx * dx + dy * dy
                          ) || 1;

                        const ux = dx / length;
                        const uy = dy / length;

                        const startX =
                          source.x +
                          ux * (nodeWidth / 2);

                        const startY =
                          source.y +
                          uy * (nodeHeight / 2);

                        const endX =
                          target.x -
                          ux * (nodeWidth / 2);

                        const endY =
                          target.y -
                          uy * (nodeHeight / 2);

                        const isSelected =
                          selectedNode &&
                          (
                            edge.source ===
                              selectedNode.id ||
                            edge.target ===
                              selectedNode.id
                          );

                        const opacity =
                          selectedNode
                            ? isSelected
                              ? 0.95
                              : 0.12
                            : 0.55;

                        const color =
                          getEdgeColor(
                            edge.relation
                          );

                        const labelX =
                          (startX + endX) / 2;

                        const labelY =
                          (startY + endY) / 2;

                        return (
                          <g
                            key={`edge-${index}`}
                            opacity={opacity}
                          >

                            <line
                              x1={startX}
                              y1={startY}
                              x2={endX}
                              y2={endY}
                              stroke={color}
                              strokeWidth={
                                isSelected ? 3 : 2
                              }
                              markerEnd={
                                edge.relation ===
                                "AFFECTS"
                                  ? "url(#reqtrace-arrow-affects)"
                                  : "url(#reqtrace-arrow)"
                              }
                            />

                            <rect
                              x={labelX - 42}
                              y={labelY - 10}
                              width="84"
                              height="20"
                              rx="3"
                              fill="#FFFDF8"
                              stroke="#D5CCBE"
                            />

                            <text
                              x={labelX}
                              y={labelY + 4}
                              textAnchor="middle"
                              fill={color}
                              fontSize="8"
                              fontWeight="700"
                              letterSpacing="0.5"
                            >
                              {edge.relation ===
                              "RELATED_TO"
                                ? `RELATED ${
                                    edge.similarity != null
                                      ? `· ${Number(
                                          edge.similarity
                                        ).toFixed(2)}`
                                      : ""
                                  }`
                                : "AFFECTS"}
                            </text>

                          </g>
                        );
                      })}

                      {/* NODES */}

                      {nodes.map((node) => {

                        const position =
                          positions[node.id];

                        if (!position) {
                          return null;
                        }

                        const isSelected =
                          selectedGraphNode ===
                          node.id;

                        const isConnected =
                          selectedNode &&
                          edges.some(
                            (edge) =>
                              (
                                edge.source ===
                                  selectedNode.id &&
                                edge.target ===
                                  node.id
                              ) ||
                              (
                                edge.target ===
                                  selectedNode.id &&
                                edge.source ===
                                  node.id
                              )
                          );

                        const dimmed =
                          selectedNode &&
                          !isSelected &&
                          !isConnected;

                        const isComponent =
                          node.node_type ===
                          "component";
 
                        return (
                          <g
                            key={node.id}
                            onClick={() =>
                              setSelectedGraphNode(
                                node.id
                              )}
                            style={{
                              cursor: "pointer",
                              opacity: dimmed
                                ? 0.28
                                : 1,
                              transition:
                                "opacity 180ms ease",
                            }}
                          >

                            <rect
                              x={
                                position.x -
                                nodeWidth / 2
                              }
                              y={
                                position.y -
                                nodeHeight / 2
                              }
                              width={nodeWidth}
                              height={nodeHeight}
                              rx="10"
                              fill={
                                isComponent
                                  ? "#F5EFE4"
                                  : "#EEF6FB"
                              }
                              stroke={
                                isSelected
                                  ? "#17324D"
                                  : isComponent
                                    ? "#8A6A3D"
                                    : "#2F6B9A"
                              }
                              strokeWidth={
                                isSelected ? 4 : 2
                              }
                            />

                            <text
                              x={
                                position.x -
                                nodeWidth / 2 +
                                14
                              }
                              y={
                                position.y -
                                24
                              }
                              fill={
                                isComponent
                                  ? "#8A6A3D"
                                  : "#2F6B9A"
                              }
                              fontSize="11"
                              fontWeight="800"
                              letterSpacing="1"
                            >
                              {node.id}
                            </text>

                            <text
                              x={
                                position.x -
                                nodeWidth / 2 +
                                14
                              }
                              y={
                                position.y -
                                4
                              }
                              fill="#18324A"
                              fontSize="10"
                              fontWeight="700"
                            >
                              {truncate(
                                node.type ||
                                  node.node_type ||
                                  "NODE",
                                24
                              )}
                            </text>

                            <text
                              x={
                                position.x -
                                nodeWidth / 2 +
                                14
                              }
                              y={
                                position.y + 16
                              }
                              fill="#52708B"
                              fontSize="9"
                            >
                              {isComponent
                                ? "AFFECTED COMPONENT"
                                : "REQUIREMENT"}
                            </text>

                          </g>
                        );
                      })}

                    </svg>

                  </div>

                  {/* LEGEND */}

                  <div
                    style={{
                      display: "flex",
                      gap: "22px",
                      flexWrap: "wrap",
                      marginTop: "16px",
                      fontSize: "10px",
                      letterSpacing: "1px",
                      color: "#52708B",
                    }}
                  >

                    <span>
                      <strong
                        style={{
                          color: "#2F6B9A",
                        }}
                      >
                        BLUE
                      </strong>{" "}
                      REQUIREMENT
                    </span>

                    <span>
                      <strong
                        style={{
                          color: "#8A6A3D",
                        }}
                      >
                        BROWN
                      </strong>{" "}
                      COMPONENT
                    </span>

                    <span>
                      <strong
                        style={{
                          color: "#2F6B9A",
                        }}
                      >
                        RELATED_TO
                      </strong>{" "}
                      NLP SIMILARITY
                    </span>

                    <span>
                      <strong
                        style={{
                          color: "#8A6A3D",
                        }}
                      >
                        AFFECTS
                      </strong>{" "}
                      COMPONENT IMPACT
                    </span>

                  </div>

                </>

              )}

            </section>

            {/* SELECTED NODE DETAILS */}

            {selectedNode && (
              <section
                className="requirements-list"
                style={{
                  marginTop: "30px",
                }}
              >

                <div
                  style={{
                    padding: "18px 0",
                    borderBottom:
                      "1px solid rgba(24,50,74,0.12)",
                    fontWeight: "600",
                    letterSpacing: "1px",
                  }}
                >
                  SELECTED NODE
                </div>

                <div
                  style={{
                    padding: "24px 0",
                  }}
                >

                  <div
                    style={{
                      display: "flex",
                      justifyContent:
                        "space-between",
                      alignItems: "center",
                      gap: "20px",
                      flexWrap: "wrap",
                      marginBottom: "15px",
                    }}
                  >

                    <div>
                      <span className="requirement-id">
                        {selectedNode.id}
                      </span>

                      <span
                        className="requirement-type"
                        style={{
                          marginLeft: "20px",
                        }}
                      >
                        {selectedNode.type ||
                          selectedNode.node_type ||
                          "NODE"}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        setSelectedGraphNode(null)
                      }
                      style={{
                        border:
                          "1px solid #D5CCBE",
                        background:
                          "#F3ECDF",
                        color: "#18324A",
                        padding: "8px 12px",
                        cursor: "pointer",
                        fontSize: "10px",
                        letterSpacing: "1px",
                      }}
                    >
                      CLOSE
                    </button>

                  </div>

                  <p
                    style={{
                      color: "#3D5265",
                      lineHeight: "1.7",
                      marginBottom: "20px",
                    }}
                  >
                    {selectedNode.text ||
                      "No node description available."}
                  </p>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "1fr 1fr",
                      gap: "20px",
                    }}
                  >

                    <div>

                      <div
                        style={{
                          fontSize: "10px",
                          letterSpacing: "2px",
                          color: "#806F5A",
                          marginBottom: "10px",
                        }}
                      >
                        RELATED REQUIREMENTS
                      </div>

                      {selectedRelated.length ? (
                        <div
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "8px",
                          }}
                        >
                          {[
                            ...new Set(
                              selectedRelated
                            ),
                          ].map((id) => (
                            <span
                              key={id}
                              style={{
                                border:
                                  "1px solid #2F6B9A",
                                color: "#2F6B9A",
                                padding:
                                  "6px 10px",
                                fontSize: "12px",
                              }}
                            >
                              {id}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span
                          style={{
                            color: "#8A8A8A",
                            fontSize: "13px",
                          }}
                        >
                          No related requirements.
                        </span>
                      )}

                    </div>

                    <div>

                      <div
                        style={{
                          fontSize: "10px",
                          letterSpacing: "2px",
                          color: "#806F5A",
                          marginBottom: "10px",
                        }}
                      >
                        AFFECTED COMPONENTS
                      </div>

                      {selectedComponents.length ? (
                        <div
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "8px",
                          }}
                        >
                          {[
                            ...new Set(
                              selectedComponents
                            ),
                          ].map((id) => (
                            <span
                              key={id}
                              style={{
                                border:
                                  "1px solid #8A6A3D",
                                color: "#8A6A3D",
                                padding:
                                  "6px 10px",
                                fontSize: "12px",
                              }}
                            >
                              {id}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span
                          style={{
                            color: "#8A8A8A",
                            fontSize: "13px",
                          }}
                        >
                          No affected components.
                        </span>
                      )}

                    </div>

                  </div>

                </div>

              </section>
            )}

            {/* REQUIREMENT DETAILS */}

            {nodes.length > 0 && (
              <section
                className="requirements-list"
                style={{
                  marginTop: "30px",
                }}
              >

                <div
                  style={{
                    padding: "18px 0",
                    borderBottom:
                      "1px solid rgba(24,50,74,0.12)",
                    fontWeight: "600",
                    letterSpacing: "1px",
                  }}
                >
                  GRAPH NODES
                </div>

                {nodes.map((node) => (
                  <button
                    type="button"
                    key={node.id}
                    onClick={() =>
                      setSelectedGraphNode(
                        node.id
                      )
                    }
                    style={{
                      width: "100%",
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "20px",
                      textAlign: "left",
                      border: "none",
                      borderBottom:
                        "1px solid rgba(24,50,74,0.08)",
                      background:
                        selectedGraphNode ===
                        node.id
                          ? "#F3ECDF"
                          : "transparent",
                      padding:
                        "18px 0",
                      cursor: "pointer",
                    }}
                  >

                    <span className="requirement-id">
                      {node.id}
                    </span>

                    <div className="requirement-content">

                      <span className="requirement-type">
                        {node.type ||
                          node.node_type ||
                          "NODE"}
                      </span>

                      <p>
                        {node.text ||
                          "Node text unavailable."}
                      </p>

                    </div>

                  </button>
                ))}

              </section>
            )}

          </main>

        </div>
      );
    }

    // =======================================================
    // IMPACT ANALYSIS
    // =======================================================

    if (dashboardModule === "impact") {

      // The comparison API returns the latest graph inside
      // compareResult.graph. Fall back to graphData so this
      // page also works after a normal SRS upload.
      const impactGraph =
        compareResult?.graph || graphData || {
          nodes: [],
          edges: [],
        };

      const impactNodes =
        impactGraph.nodes || [];

      const impactEdges =
        impactGraph.edges || [];

      const addedRequirements =
        compareResult?.added || [];

      const deletedRequirements =
        compareResult?.deleted || [];

      const modifiedRequirements =
        compareResult?.modified || [];

      const getRequirementId = (item) => {
        if (!item) return "UNKNOWN";

        if (typeof item === "string") {
          const match = item.match(
            /\bREQ[-_ ]?\d+\b/i
          );

          return match
            ? match[0]
                .replace(/_/g, "-")
                .replace(/ /g, "-")
                .toUpperCase()
            : "UNKNOWN";
        }

        return (
          item.id ||
          item.requirement_id ||
          "UNKNOWN"
        );
      };

      const getRequirementText = (item) => {
        if (!item) return "";

        if (typeof item === "string") {
          return item;
        }

        return (
          item.text ||
          item.new ||
          item.old ||
          ""
        );
      };

      const getAffectedComponents = (
        requirementId
      ) => {

        const componentIds =
          impactEdges
            .filter(
              (edge) =>
                edge.source === requirementId &&
                edge.relation === "AFFECTS"
            )
            .map(
              (edge) => edge.target
            );

        return impactNodes.filter(
          (node) =>
            node.node_type === "component" &&
            componentIds.includes(node.id)
        );
      };

      const getRelatedRequirements = (
        requirementId
      ) => {

        const related = [];

        impactEdges.forEach(
          (edge) => {

            if (
              edge.relation !==
              "RELATED_TO"
            ) {
              return;
            }

            if (
              edge.source ===
              requirementId
            ) {
              related.push(
                edge.target
              );
            }

            if (
              edge.target ===
              requirementId
            ) {
              related.push(
                edge.source
              );
            }

          }
        );

        return [
          ...new Set(related),
        ];
      };

      const impactItems = [
        ...modifiedRequirements.map(
          (item) => ({
            id:
              item.id ||
              item.requirement_id ||
              getRequirementId(
                item.new || item.old
              ),
            type: "MODIFIED",
            oldText:
              item.old || "",
            newText:
              item.new || "",
          })
        ),

        ...deletedRequirements.map(
          (item) => ({
            id:
              getRequirementId(item),
            type: "DELETED",
            oldText:
              getRequirementText(item),
            newText: "",
          })
        ),

        ...addedRequirements.map(
          (item) => ({
            id:
              getRequirementId(item),
            type: "ADDED",
            oldText: "",
            newText:
              getRequirementText(item),
          })
        ),
      ];

      const getImpactLevel = (item) => {
  const components = getAffectedComponents(item.id);

  if (
    item.type === "MODIFIED" &&
    components.length > 0
  ) {
    return "HIGH";
  }

  if (item.type === "MODIFIED") {
    return "MEDIUM";
  }

  if (item.type === "ADDED") {
    return "MEDIUM";
  }

  if (item.type === "DELETED") {
    return "LOW";
  }

  return "LOW";
};

      const totalChanges =
        impactItems.length;

      const affectedComponentIds =
        [];

      impactItems.forEach(
        (item) => {

          getAffectedComponents(
            item.id
          ).forEach(
            (component) => {

              if (
                !affectedComponentIds.includes(
                  component.id
                )
              ) {
                affectedComponentIds.push(
                  component.id
                );
              }

            }
          );

        }
      );

      const totalAffectedComponents =
  compareResult?.impact_summary?.affected_components ??
  affectedComponentIds.length;

      const highImpactCount =
        impactItems.filter(
          (item) =>
            getImpactLevel(item) ===
            "HIGH"
        ).length;

      return (
        <div className="dashboard-page">

          <header className="dashboard-header">

            <button
              className="dashboard-logo"
              onClick={backToModules}
            >
              <span className="dashboard-logo-box">
                R
              </span>

              <span className="dashboard-logo-text">
                REQTRACE <span>AI</span>
              </span>
            </button>

            <nav className="dashboard-nav">

              <button
                onClick={backToModules}
              >
                DASHBOARD
              </button>

              <button
                onClick={goHome}
              >
                HOME
              </button>

            </nav>

          </header>


          <main className="dashboard-main">

            <button
              className="back-home-button"
              onClick={backToModules}
            >
              ← BACK TO MODULES
            </button>


            <section className="dashboard-intro">

              <div>

                <div className="dashboard-eyebrow">
                  TRACEABILITY
                </div>

                <h1>
                  Trace.
                  <br />
                  <span>Impact.</span>
                </h1>

                <p>
                  Analyze requirement changes,
                  trace related requirements,
                  and identify potentially
                  affected software components.
                </p>

              </div>

            </section>


            {!compareResult ? (

              <section
                style={{
                  marginTop: "35px",
                  padding: "60px 40px",
                  textAlign: "center",
                  border:
                    "1px solid #d8cdbb",
                  background:
                    "#fffdf8",
                }}
              >

                <div
                  style={{
                    fontSize: "12px",
                    letterSpacing: "3px",
                    color: "#2f75ad",
                    marginBottom: "18px",
                  }}
                >
                  IMPACT ANALYSIS
                </div>

                <h2
                  style={{
                    color: "#17324d",
                    fontSize: "30px",
                    marginBottom: "15px",
                  }}
                >
                  Compare two SRS versions first.
                </h2>

                <p
                  style={{
                    color: "#52708b",
                    lineHeight: "1.7",
                    maxWidth: "650px",
                    margin: "0 auto",
                  }}
                >
                  Upload an old and new SRS
                  version in Version Comparison.
                  The detected changes will then
                  be traced through the Knowledge
                  Graph here.
                </p>

                <button
                  className="analyze-button"
                  onClick={() =>
                    openModule("compare")
                  }
                  style={{
                    marginTop: "30px",
                  }}
                >
                  GO TO VERSION COMPARISON
                  <span>→</span>
                </button>

              </section>

            ) : (

              <>

                <section
                  className="result-summary"
                  style={{
                    marginTop: "35px",
                  }}
                >

                  <div>
                    <span>
                      TOTAL CHANGES
                    </span>

                    <strong>
                      {totalChanges}
                    </strong>
                  </div>

                  <div>
                    <span>
                      MODIFIED
                    </span>

                    <strong>
                      {modifiedRequirements.length}
                    </strong>
                  </div>

                  <div>
                    <span>
                      AFFECTED COMPONENTS
                    </span>

                    <strong>
                      {totalAffectedComponents}
                    </strong>
                  </div>

                  <div>
                    <span>
                      HIGH IMPACT
                    </span>

                    <strong>
                      {highImpactCount}
                    </strong>
                  </div>

                </section>


                <section
                  className="requirements-list"
                  style={{
                    marginTop: "35px",
                  }}
                >

                  <div
                    style={{
                      padding: "20px 0",
                      borderBottom:
                        "1px solid rgba(24,50,74,0.12)",
                      fontWeight: "600",
                      letterSpacing: "1px",
                    }}
                  >
                    REQUIREMENT IMPACT ANALYSIS
                  </div>


                  {impactItems.length === 0 ? (

                    <div
                      className="empty-result"
                    >
                      No requirement changes
                      were detected.
                    </div>

                  ) : (

                    impactItems.map(
                      (item, index) => {

                        const related =
                          getRelatedRequirements(
                            item.id
                          );

                        const components =
                          getAffectedComponents(
                            item.id
                          );

                        const impactLevel =
                          getImpactLevel(
                            item
                          );

                        return (
                          <div
                            className="requirement-row"
                            key={`${item.id}-${index}`}
                            style={{
                              display: "block",
                              padding:
                                "28px 0",
                            }}
                          >

                            <div
                              style={{
                                display: "flex",
                                justifyContent:
                                  "space-between",
                                alignItems:
                                  "center",
                                gap: "20px",
                                marginBottom:
                                  "18px",
                              }}
                            >

                              <div>

                                <span
                                  className="requirement-id"
                                >
                                  {item.id}
                                </span>

                                <span
                                  className="requirement-type"
                                  style={{
                                    marginLeft:
                                      "20px",
                                  }}
                                >
                                  {item.type}
                                </span>

                              </div>

                              <span
                                style={{
                                  border:
                                    "1px solid #2f75ad",
                                  color:
                                    "#2f75ad",
                                  padding:
                                    "7px 12px",
                                  fontSize:
                                    "11px",
                                  letterSpacing:
                                    "1.5px",
                                }}
                              >
                                {impactLevel} IMPACT
                              </span>

                            </div>


                            {item.oldText && (

                              <div
                                style={{
                                  padding:
                                    "16px",
                                  marginBottom:
                                    "12px",
                                  background:
                                    "#f5efe4",
                                  borderLeft:
                                    "3px solid #b9aa95",
                                }}
                              >

                                <div
                                  style={{
                                    fontSize:
                                      "10px",
                                    letterSpacing:
                                      "2px",
                                    marginBottom:
                                      "8px",
                                    color:
                                      "#806f5a",
                                  }}
                                >
                                  PREVIOUS VERSION
                                </div>

                                <p
                                  style={{
                                    margin: 0,
                                    lineHeight:
                                      "1.6",
                                  }}
                                >
                                  {item.oldText}
                                </p>

                              </div>

                            )}


                            {item.newText && (

                              <div
                                style={{
                                  padding:
                                    "16px",
                                  marginBottom:
                                    "18px",
                                  background:
                                    "#eef6fb",
                                  borderLeft:
                                    "3px solid #2f75ad",
                                }}
                              >

                                <div
                                  style={{
                                    fontSize:
                                      "10px",
                                    letterSpacing:
                                      "2px",
                                    marginBottom:
                                      "8px",
                                    color:
                                      "#2f75ad",
                                  }}
                                >
                                  CURRENT VERSION
                                </div>

                                <p
                                  style={{
                                    margin: 0,
                                    lineHeight:
                                      "1.6",
                                  }}
                                >
                                  {item.newText}
                                </p>

                              </div>

                            )}


                            <div
                              style={{
                                display:
                                  "grid",
                                gridTemplateColumns:
                                  "1fr 1fr",
                                gap: "20px",
                              }}
                            >

                              <div>

                                <div
                                  style={{
                                    fontSize:
                                      "10px",
                                    letterSpacing:
                                      "2px",
                                    color:
                                      "#806f5a",
                                    marginBottom:
                                      "10px",
                                  }}
                                >
                                  RELATED REQUIREMENTS
                                </div>

                                {related.length >
                                0 ? (

                                  <div
                                    style={{
                                      display:
                                        "flex",
                                      flexWrap:
                                        "wrap",
                                      gap: "8px",
                                    }}
                                  >

                                    {related.map(
                                      (reqId) => (
                                        <span
                                          key={reqId}
                                          style={{
                                            border:
                                              "1px solid #2f75ad",
                                            color:
                                              "#2f75ad",
                                            padding:
                                              "6px 10px",
                                            fontSize:
                                              "12px",
                                          }}
                                        >
                                          {reqId}
                                        </span>
                                      )
                                    )}

                                  </div>

                                ) : (

                                  <span
                                    style={{
                                      color:
                                        "#8a8a8a",
                                      fontSize:
                                        "13px",
                                    }}
                                  >
                                    No related
                                    requirements.
                                  </span>

                                )}

                              </div>


                              <div>

                                <div
                                  style={{
                                    fontSize:
                                      "10px",
                                    letterSpacing:
                                      "2px",
                                    color:
                                      "#806f5a",
                                    marginBottom:
                                      "10px",
                                  }}
                                >
                                  AFFECTED COMPONENTS
                                </div>

                                {components.length >
                                0 ? (

                                  <div
                                    style={{
                                      display:
                                        "flex",
                                      flexDirection:
                                        "column",
                                      gap: "8px",
                                    }}
                                  >

                                    {components.map(
                                      (component) => (
                                        <div
                                          key={
                                            component.id
                                          }
                                          style={{
                                            border:
                                              "1px solid #d8cdbb",
                                            padding:
                                              "10px 12px",
                                            color:
                                              "#17324d",
                                            background:
                                              "#fffdf8",
                                            fontSize:
                                              "13px",
                                          }}
                                        >
                                          {
                                            component.text
                                          }
                                        </div>
                                      )
                                    )}

                                  </div>

                                ) : (

                                  <span
                                    style={{
                                      color:
                                        "#8a8a8a",
                                      fontSize:
                                        "13px",
                                    }}
                                  >
                                    No affected
                                    components
                                    found.
                                  </span>

                                )}

                              </div>

                            </div>

                          </div>
                        );

                      }
                    )

                  )}

                </section>


                <section
                  style={{
                    marginTop: "30px",
                    padding: "30px",
                    background:
                      "#f5efe4",
                    border:
                      "1px solid #d8cdbb",
                  }}
                >

                  <div
                    style={{
                      fontSize: "11px",
                      letterSpacing: "3px",
                      color: "#2f75ad",
                      marginBottom:
                        "10px",
                    }}
                  >
                    ANALYSIS RESULT
                  </div>

                  <h2
                    style={{
                      margin:
                        "0 0 12px",
                      color:
                        "#17324d",
                    }}
                  >
                    Impact analysis completed.
                  </h2>

                  <p
                    style={{
                      margin: 0,
                      color:
                        "#52708b",
                      lineHeight:
                        "1.7",
                    }}
                  >
                    Requirement changes have
                    been traced through the
                    Knowledge Graph. Related
                    requirements and mapped
                    software components are
                    shown above.
                  </p>

                </section>

              </>

            )}

          </main>

        </div>
      );
    }
  }

  // =========================================================
  // LANDING PAGE
  // =========================================================

  return (
    <div className="page">
      {toast && (
  <div className="reqtrace-toast">
    <span className="toast-icon">✓</span>
    <span>{toast}</span>
  </div>
)}

      <header className="header">

        <div className="logo">

          <div className="logo-box">
            R
          </div>

          <div className="logo-text">
            REQTRACE <span>AI</span>
          </div>

        </div>

        <nav className="nav">

          <a href="#about">
            ABOUT
          </a>

          <a href="#faq">
            FAQ
          </a>
<button
  className="nav-signin"
  onClick={() => {
    setAuthMode("login");

    document.getElementById("login")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }}
>
  SIGN IN
</button>

        </nav>

      </header>

      <main className="main">

        <section
          className="intro"
          id="about"
        >

          <div className="eyebrow">
            AI-BASED SOFTWARE REQUIREMENT ANALYSIS
          </div>

          <h1>
            Understand.
            <br />

            <span>
              Trace.
            </span>

            <br />

            Evolve.
          </h1>

          <p>
            ReqTrace AI transforms software
            requirements into structured insights
            through intelligent extraction,
            requirement comparison, traceability
            and knowledge graph analysis.
          </p>

          <div className="intro-line"></div>

          <div className="features">

            <div className="feature">

              <span className="feature-number">
                01
              </span>

              <span>
                REQUIREMENT
                <br />
                EXTRACTION
              </span>

            </div>

            <div className="feature">

              <span className="feature-number">
                02
              </span>

              <span>
                VERSION
                <br />
                COMPARISON
              </span>

            </div>

            <div className="feature">

              <span className="feature-number">
                03
              </span>

              <span>
                KNOWLEDGE
                <br />
                GRAPH
              </span>

            </div>

          </div>

        </section>

        <section
  className="auth-wrapper"
  id="login"
>
  <div className="auth-card">

   <div className="auth-label">
  {authMode === "login"
    ? "WELCOME BACK"
    : "GET STARTED"}
</div>

<h2>
  {authMode === "login"
    ? "Sign in."
    : "Create account."}
</h2>

<p className="auth-description">
  {authMode === "login"
    ? "Sign in to access your requirement workspace."
    : "Create your ReqTrace AI account."}
</p>

    <form
      onSubmit={async (event) => {
        event.preventDefault();

        const email =
          event.currentTarget.email.value.trim();

       const name =
  event.currentTarget.elements.name?.value.trim();

        const password =
          event.currentTarget.password.value;

        try {
          const response = await fetch(
            authMode === "login"
  ? "http://127.0.0.1:8000/auth/login"
  : "http://127.0.0.1:8000/auth/register",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
              },
             "body": JSON.stringify(
  authMode === "login"
    ? {
        email: email,
        password: password,
      }
    : {
        name: name,
        email: email,
        password: password,
      }
),
            }
          );

          const data = await response.json();

          if (!response.ok) {
            alert(
              data.detail ||
              "Invalid email or password."
            );
            return;
          }

                    if (authMode === "register") {
            alert(
              "Account created successfully. Please sign in."
            );

            setAuthMode("login");
            

            return;
          }

          // Save JWT token
          localStorage.setItem(
            "reqtrace_token",
            data.access_token
          );

          // Save user information
          localStorage.setItem(
            "reqtrace_user",
            JSON.stringify(data.user)
          );

          // Login successful
          openDashboard();

        } catch (error) {

          console.error(
            "Login error:",
            error
          );

          alert(
            "Cannot connect to backend. " +
            "Make sure FastAPI is running."
          );
        }
      }}
    >
      {authMode === "register" && (
  <div className="field">

    <label>
      FULL NAME
    </label>

    <input
      type="text"
      name="name"
      placeholder="Your name"
      required
    />

  </div>
)}
      <div className="field">

        <label>
          EMAIL ADDRESS
        </label>

        <input
          type="email"
          name="email"
          placeholder="you@example.com"
          required
        />

      </div>

      <div className="field">

        <label>
          PASSWORD
        </label>

        <input
          type="password"
          name="password"
          placeholder="Your password"
          required
        />

      </div>

    <button 
  type="submit" 
  className="auth-button" 
> 

  <span>
    {authMode === "login"
      ? "SIGN IN"
      : "CREATE ACCOUNT"}
  </span>

  <span className="arrow"> 
    →
  </span> 

</button>
    </form>

    <div className="switch">

  <span>
    Don't have an account?
  </span>

<button
  type="button"
  onClick={() => {
    setAuthMode("register");

    document
      .getElementById("login")
      ?.scrollIntoView({ behavior: "smooth" });
  }}
>
  Create account
</button>
</div>

  </div>
</section>

      </main>

      {/* FAQ */}

      <section
        className="faq-section"
        id="faq"
      >

        <div className="faq-heading">

          <div className="faq-number">
            05
          </div>

          <div>

            <div className="faq-label">
              KNOWLEDGE BASE
            </div>

            <h2>
              Frequently Asked
              <br />

              <span>
                Questions.
              </span>
            </h2>

          </div>

        </div>

        <div className="faq-list">

          {faqs.map(
            (faq, index) => (

              <div
                className={`faq-item ${
                  openFAQ === index
                    ? "active"
                    : ""
                }`}
                key={index}
              >

                <button
                  className="faq-question"
                  onClick={() =>
                    toggleFAQ(index)
                  }
                >

                  <div className="faq-question-left">

                    <span className="faq-index">
                      0{index + 1}
                    </span>

                    <span>
                      {faq.question}
                    </span>

                  </div>

                  <span className="faq-icon">

                    {openFAQ === index
                      ? "−"
                      : "+"}

                  </span>

                </button>

                <div
                  className={`faq-answer ${
                    openFAQ === index
                      ? "show"
                      : ""
                  }`}
                >

                  <p>
                    {faq.answer}
                  </p>

                </div>

              </div>
            )
          )}

        </div>

      </section>

            {/* FOOTER */}

      <footer className="footer">

        <div className="footer-question">
          ReqTrace AI — intelligent requirement
          traceability.
        </div>

        <div className="footer-links">

          <div className="footer-column">

            <button
              type="button"
              onClick={() =>
                showToast(
                  "ReqTrace AI — intelligent requirement traceability."
                )
              }
            >
              About ReqTrace AI
            </button>

            <button
              type="button"
              onClick={() =>
                showToast(
                  "Requirement Analysis is available in the dashboard."
                )
              }
            >
              Requirement Analysis
            </button>

            <button
              type="button"
              onClick={() =>
                showToast(
                  "Knowledge Graph is available in the dashboard."
                )
              }
            >
              Knowledge Graph
            </button>

            <button
              type="button"
              onClick={() =>
                showToast(
                  "Traceability is available in the dashboard."
                )
              }
            >
              Traceability
            </button>

          </div>


          <div className="footer-column">

            <button
              type="button"
              onClick={() =>
                showToast(
                  "Document Processing is available in the dashboard."
                )
              }
            >
              Document Processing
            </button>

            <button
              type="button"
              onClick={() =>
                showToast(
                  "Version Comparison is available in the dashboard."
                )
              }
            >
              Version Comparison
            </button>

            <button
              type="button"
              onClick={() =>
                showToast(
                  "Impact Analysis is available in the dashboard."
                )
              }
            >
              Impact Analysis
            </button>

            <button
              type="button"
              onClick={() =>
                showToast(
                  "Project Documentation will be available here."
                )
              }
            >
              Project Documentation
            </button>

          </div>


          <div className="footer-column">

            <button
              type="button"
              onClick={openDashboard}
            >
              Sign In
            </button>

            <button
              type="button"
              onClick={openDashboard}
            >
              Create Account
            </button>

            <button
              type="button"
              onClick={() =>
                showToast(
                  "Help is available through the ReqTrace AI dashboard."
                )
              }
            >
              Help
            </button>

            <button
              type="button"
              onClick={() =>
                showToast(
                  "FAQ — scroll up to view frequently asked questions."
                )
              }
            >
              FAQ
            </button>

          </div>

        </div>


        <div className="footer-bottom">

          <button className="language">
            ◉ English <span>⌄</span>
          </button>

          <div className="footer-brand">

            <div className="footer-r">
              R
            </div>

            <span>
              REQTRACE AI
            </span>

          </div>

        </div>


        <div className="footer-note">
          AI-BASED SOFTWARE REQUIREMENT ANALYSIS &
          KNOWLEDGE GRAPH SYSTEM.
        </div>

      </footer>

    </div>
  );
}

export default App;
import React, { useState, useEffect } from "react";
import { Viewer, Worker } from "@react-pdf-viewer/core";
import "@react-pdf-viewer/core/lib/styles/index.css";
import axios from "axios";
import { Typography, TextField, Button, Select, MenuItem, Card, CardContent, Grid } from "@mui/material";
import { CircularProgress } from "@mui/material";


export default function MarketAnalyzer() {
  const [pdfFiles] = useState([
    { id: "pdf1", name: "2023 ConocoPhillips AIM Presentation", filename: "2023-conocophillips-aim-presentation.pdf" },
    { id: "pdf2", name: "2024 ConocoPhillips Proxy Statement", filename: "2024-conocophillips-proxy-statement.pdf" },
  ]);

  const [selectedPdf1, setSelectedPdf1] = useState(pdfFiles[0].id);
  const [selectedPdf2, setSelectedPdf2] = useState(pdfFiles[1].id);
  const [summaries, setSummaries] = useState({});
  const [query, setQuery] = useState("");
  const [comparisonQuery, setComparisonQuery] = useState("");
  const [selectedSearchPdf, setSelectedSearchPdf] = useState(pdfFiles[0].id);

  const [result, setResult] = useState("");
  const [sourceChunks, setSourceChunks] = useState([]);
  const [comparisonResult, setComparisonResult] = useState("");
  const [comparisonSources, setComparisonSources] = useState({ pdf1: [], pdf2: [] });

  const [expandedChunk, setExpandedChunk] = useState(null);

  // Add loading states
  const [searchLoading, setSearchLoading] = useState(false);
  const [comparisonLoading, setComparisonLoading] = useState(false);

  const BACKEND_URL = "http://localhost:8080";
  //const BACKEND_URL = "https://rag-backend-latest-792544276770.us-central1.run.app";
  const GCS_BUCKET_URL = "https://storage.googleapis.com/rag-frontend-bucket/pdfs";

  // Fetch summaries on load
  useEffect(() => {
    const fetchSummaries = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/rag/summaries`);
        setSummaries(response.data.summaries);
      } catch (error) {
        console.error("Error fetching summaries:", error);
      }
    };
    fetchSummaries();
  }, []);

  // Handle AI-Powered Search
  const handleSearch = async () => {
    if (!query.trim()) {
      alert("Please enter a search query.");
      return;
    }
    setSearchLoading(true); // Start loading
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/rag/search/`,
        { query, pdf_id: selectedSearchPdf, top_k: 6 },
        { headers: { "Content-Type": "application/json" } }
      );
      setResult(response.data.answer);
      setSourceChunks(response.data.source_chunks);
    } catch (error) {
      console.error("Error fetching data:", error);
      setResult("Error: Unable to fetch data. Check console for details.");
    }finally {
      setSearchLoading(false); // Stop loading
    }
  };

  // Handle Comparison Search
  const handleCompareSearch = async () => {
    if (!comparisonQuery.trim()) {
      alert("Please enter a search query for comparison.");
      return;
    }
    const requestData = {
      query: comparisonQuery,
      pdf1_id: selectedPdf1,
      pdf2_id: selectedPdf2,
      top_k: 6,
    };
    setComparisonLoading(true); // Start loading
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/rag/compare/`,
        requestData,
        { headers: { "Content-Type": "application/json" } }
      );
      setComparisonResult(response.data.response);
      setComparisonSources({
        pdf1: response.data.source_chunks_pdf1 || [],
        pdf2: response.data.source_chunks_pdf2 || [],
      });
    } catch (error) {
      console.error("Error fetching comparison data:", error);
      setComparisonResult("Error: Unable to fetch comparison data.");
    }finally {
      setComparisonLoading(false); // Stop loading
    }
  };

  // Toggle Content Expansion
  const handleChunkClick = (id) => {
    setExpandedChunk(expandedChunk === id ? null : id);
  };

  // Construct URLs for PDF Viewers
  const selectedPdf1Data = pdfFiles.find((pdf) => pdf.id === selectedPdf1);
  const selectedPdf2Data = pdfFiles.find((pdf) => pdf.id === selectedPdf2);
  const pdf1Url = selectedPdf1Data ? `${GCS_BUCKET_URL}/${selectedPdf1Data.filename}` : null;
  const pdf2Url = selectedPdf2Data ? `${GCS_BUCKET_URL}/${selectedPdf2Data.filename}` : null;

  return (
    <div style={{
      maxWidth: "100%",
      minHeight: "100vh",
      margin: "0",
      padding: "0",
      fontFamily: "Arial",
      background: "#ffffff",
      display: "flex",
      flexDirection: "column"
    }}>
      <Typography
        variant="h3"
        style={{
          fontFamily: "'Playfair Display', serif", // Stylish font
          fontWeight: 700, // Bold
          textAlign: "center",
          color: "#fca311",
          textShadow: "2px 2px 4px rgba(0, 0, 0, 0)", // Soft shadow for style
          letterSpacing: "2px", // Add spacing for elegance
          marginBottom: "30px",
        }}
      >
        AI-Powered Market Analyzer
      </Typography>

      {/* PDF Viewers */}
      <Grid container spacing={2}>
        {/* PDF 1 */}
        <Grid item xs={6}>
          <div className="global-box">
            <Typography variant="h6" className="unselectable">{selectedPdf1Data?.name}</Typography>
          </div>


          <div style={{ border: "1px solid #ccc", padding: "10px", height: "500px" }}>
            {pdf1Url ? (
              <Worker workerUrl="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js">
                <Viewer fileUrl={pdf1Url} />
              </Worker>
            ) : (
              <p>Loading PDF 1...</p>
            )}
          </div>

          <Card className="global-box">
            <CardContent>
              <Typography variant="h6" style={{ fontWeight: "bold" }}>
                📄 Summary (PDF 1):
              </Typography>
              <Typography variant="body2" style={{ whiteSpace: "pre-line", marginTop: "10px" }}>
                {summaries[selectedPdf1] || "Loading summary..."}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* PDF 2 */}
        <Grid item xs={6}>
          <div className="global-box">
            <Typography variant="h6" className="unselectable">{selectedPdf2Data?.name}</Typography>
          </div>


          <div style={{ border: "1px solid #ccc", padding: "10px", height: "500px" }}>
            {pdf2Url ? (
              <Worker workerUrl="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js">
                <Viewer fileUrl={pdf2Url} />
              </Worker>
            ) : (
              <p>Loading PDF 2...</p>
            )}
          </div>

          <Card className="global-box">
            <CardContent>
              <Typography variant="h6" style={{ fontWeight: "bold" }}>
                📄 Summary (PDF 2):
              </Typography>
              <Typography variant="body2" style={{ whiteSpace: "pre-line", marginTop: "10px" }}>
                {summaries[selectedPdf2] || "Loading summary..."}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* PDF Selector for Search */}
      <div className="global-box">
          <Typography
            variant="subtitle1"
            style={{
              fontWeight: "bold",
              marginBottom: "8px",
              fontSize: "1.2rem",
            }}
          >
          Choose a PDF document to analyze:
        </Typography>
          <Select
            value={selectedSearchPdf}
            onChange={(e) => setSelectedSearchPdf(e.target.value)}
            fullWidth
            style={{ marginBottom: "10px" }}
          >
            {pdfFiles.map((file) => (
                <MenuItem key={file.id} value={file.id}>
                    {file.name}
                </MenuItem>
            ))}
          </Select>


          {/* AI-Powered Search */}
          <TextField
            label="Ask something about the reports..."
            variant="outlined"
            fullWidth
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ margin: "20px 0" }}
          />
      </div>

      <div className="centered-buttons">
        <Button variant="contained" color="primary" onClick={handleSearch}
          className="small-button"
        >
          Search
        </Button>
      </div>

      {/* ✅ Display Loading Indicator for Single Search */}
      {searchLoading && (
        <div style={{ display: "flex", justifyContent: "center", margin: "20px 0" }}>
          <CircularProgress style={{ color: "#fca311" }} size={40} />
          <Typography variant="h6" style={{ marginLeft: "10px", fontWeight: "bold", color: "#fca311" }}>
            Generating results... Please wait.
          </Typography>
        </div>
      )}

      {/* Single PDF Search Results */}
      {result && (
        <Card className="global-box">
          <CardContent>
            <Typography variant="h6" style={{ fontWeight: "bold" }}>
              🔍 AI Response:
            </Typography>
            <Typography variant="body1" style={{ whiteSpace: "pre-line", marginTop: "10px" }}>
              {result || "Loading ..."}
            </Typography>

            <Typography variant="body1" style={{ marginTop: "20px", fontWeight: "bold" }}>
              📖 Source Data (Click to Expand):
            </Typography>
            <ul>
              {sourceChunks.map((chunk, index) => (
                <li
                  key={index}
                  className="source-chunk"
                  onClick={() => handleChunkClick(index)}
                >
                  {chunk.Page && chunk.Page.toLowerCase() !== "unknown"
                    ? `Source ${index + 1} (Page ${chunk.Page})`
                    : `Source ${index + 1}`}

                  {expandedChunk === index && (
                    <Typography
                      variant="body2"
                    >
                      {chunk.Content}
                    </Typography>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="global-box">
          {/* Comparison Search */}
          <TextField
            label="Compare across two PDFs..."
            variant="outlined"
            fullWidth
            value={comparisonQuery}
            onChange={(e) => setComparisonQuery(e.target.value)}
            style={{ margin: "20px 0" }}
          />
      </div>

      <div className="centered-buttons">
        <Button variant="contained" color="secondary" onClick={handleCompareSearch}
          className="small-button"
        >
          Compare Two PDFs
        </Button>
      </div>

      {/* ✅ Display Loading Indicator for Comparison */}
      {comparisonLoading && (
        <div style={{ display: "flex", justifyContent: "center", margin: "20px 0" }}>
          <CircularProgress style={{ color: "#fca311" }} size={40} />
          <Typography variant="h6" style={{ marginLeft: "10px", fontWeight: "bold", color: "#fca311" }}>
            Comparing documents... Please wait.
          </Typography>
        </div>
      )}

      {/* Comparison Results */}
      {comparisonResult && (
        <Card className="global-box">
          <CardContent>
            <Typography variant="h6" style={{ fontWeight: "bold" }}>
              📊 AI Response (Cross-PDF Comparison):
            </Typography>
            <Typography variant="body1" style={{ whiteSpace: "pre-line", marginTop: "10px" }}>
              {comparisonResult}
            </Typography>

            <Typography variant="body1" style={{ marginTop: "20px", fontWeight: "bold" }}>
              📖 Comparison Source Data (Click to Expand):
            </Typography>

            <ul>
              {comparisonSources.pdf1.map((chunk, index) => (
                <li
                  key={`pdf1-${index}`}
                  className="source-chunk"
                  onClick={() => handleChunkClick(`pdf1-${index}`)}
                >
                  {chunk.Page && chunk.Page.toLowerCase() !== "unknown"
                    ? `Source ${index + 1} (PDF 1, Page ${chunk.Page})`
                    : `Source ${index + 1} (PDF 1)`}

                  {expandedChunk === `pdf1-${index}` && (
                    <Typography variant="body2">
                      {chunk.Content}
                    </Typography>
                  )}
                </li>
              ))}


              {comparisonSources.pdf2.map((chunk, index) => (
                <li
                  key={`pdf2-${index}`}
                  className="source-chunk"
                  onClick={() => handleChunkClick(`pdf2-${index}`)}
                >
                  {chunk.Page && chunk.Page.toLowerCase() !== "unknown"
                    ? `Source ${index + 1} (PDF 2, Page ${chunk.Page})`
                    : `Source ${index + 1} (PDF 2)`}

                  {expandedChunk === `pdf2-${index}` && (
                    <Typography variant="body2">
                      {chunk.Content}
                    </Typography>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

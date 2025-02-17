import React, { useState, useEffect } from "react";
import { Viewer, Worker } from "@react-pdf-viewer/core";
import "@react-pdf-viewer/core/lib/styles/index.css";
import axios from "axios";
import { Typography, TextField, Button, Select, MenuItem, Card, CardContent, Grid } from "@mui/material";

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

  // const BACKEND_URL = "http://localhost:8080";
  const BACKEND_URL = "https://rag-market-analyzer-792544276770.us-central1.run.app";
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
    <div style={{ maxWidth: "1200px", margin: "auto", fontFamily: "Arial" }}>
      <Typography
        variant="h5"
        style={{
          fontFamily: "Georgia, serif",
          fontWeight: "bold",
          textAlign: "center",
          marginBottom: "20px",
        }}
      >
        AI-Powered Market Analyzer
      </Typography>

      {/* PDF Viewers */}
      <Grid container spacing={2}>
        {/* PDF 1 */}
        <Grid item xs={6}>
          <Select
            value={selectedPdf1}
            onChange={(e) => setSelectedPdf1(e.target.value)}
            fullWidth
            style={{ marginBottom: "10px" }}
          >
            {pdfFiles.map((file) => (
              <MenuItem key={file.id} value={file.id}>
                {file.name}
              </MenuItem>
            ))}
          </Select>

          <div style={{ border: "1px solid #ccc", padding: "10px", height: "500px" }}>
            {pdf1Url ? (
              <Worker workerUrl="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js">
                <Viewer fileUrl={pdf1Url} />
              </Worker>
            ) : (
              <p>Loading PDF 1...</p>
            )}
          </div>

          <Card style={{ marginTop: "20px", padding: "15px" }}>
            <CardContent>
              <Typography variant="h6" style={{ fontWeight: "bold" }}>
                📄 Summary (PDF 1):
              </Typography>
              <Typography variant="body2" style={{ whiteSpace: "pre-line" }}>
                {summaries[selectedPdf1] || "Loading summary..."}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* PDF 2 */}
        <Grid item xs={6}>
          <Select
            value={selectedPdf2}
            onChange={(e) => setSelectedPdf2(e.target.value)}
            fullWidth
            style={{ marginBottom: "10px" }}
          >
            {pdfFiles.map((file) => (
              <MenuItem key={file.id} value={file.id}>
                {file.name}
              </MenuItem>
            ))}
          </Select>

          <div style={{ border: "1px solid #ccc", padding: "10px", height: "500px" }}>
            {pdf2Url ? (
              <Worker workerUrl="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js">
                <Viewer fileUrl={pdf2Url} />
              </Worker>
            ) : (
              <p>Loading PDF 2...</p>
            )}
          </div>

          <Card style={{ marginTop: "20px", padding: "15px" }}>
            <CardContent>
              <Typography variant="h6" style={{ fontWeight: "bold" }}>
                📄 Summary (PDF 2):
              </Typography>
              <Typography variant="body2" style={{ whiteSpace: "pre-line" }}>
                {summaries[selectedPdf2] || "Loading summary..."}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* PDF Selector for Search */}
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

      <Button variant="contained" color="primary" fullWidth onClick={handleSearch}>
        Search
      </Button>

      {/* Single PDF Search Results */}
      {result && (
        <Card style={{ marginTop: "20px", padding: "15px" }}>
          <CardContent>
            <Typography variant="h6" style={{ fontWeight: "bold" }}>
              🔍 AI Response:
            </Typography>
            <Typography variant="body1" style={{ whiteSpace: "pre-line", marginTop: "10px" }}>
              {result}
            </Typography>

            <Typography variant="body1" style={{ marginTop: "20px", fontWeight: "bold" }}>
              📖 Source Data (Click to Expand):
            </Typography>
            <ul>
              {sourceChunks.map((chunk, index) => (
                <li
                  key={index}
                  onClick={() => handleChunkClick(index)}
                  style={{
                    cursor: "pointer",
                    color: "blue",
                    textDecoration: "underline",
                    marginBottom: "5px",
                  }}
                >
                  {chunk.Content.replace(/\[Page\s*Unknown\]/gi, "").substring(0, 100)}...
                  {chunk.Content.substring(0, 100)}...
                  {expandedChunk === index && (
                    <Typography
                      variant="body2"
                      style={{
                        whiteSpace: "pre-line",
                        color: "black",
                        marginTop: "5px",
                      }}
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

      {/* Comparison Search */}
      <TextField
        label="Compare across two PDFs..."
        variant="outlined"
        fullWidth
        value={comparisonQuery}
        onChange={(e) => setComparisonQuery(e.target.value)}
        style={{ margin: "20px 0" }}
      />

      <Button variant="contained" color="secondary" fullWidth onClick={handleCompareSearch}>
        Compare Two PDFs
      </Button>

      {/* Comparison Results */}
      {comparisonResult && (
        <Card style={{ marginTop: "20px", padding: "15px" }}>
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
                  onClick={() => handleChunkClick(`pdf1-${index}`)}
                  style={{
                    cursor: "pointer",
                    color: "blue",
                    textDecoration: "underline",
                    marginBottom: "5px",
                  }}
                >
                  <b>
                    {chunk.Page && chunk.Page.toLowerCase() !== "unknown"
                        ? `Page ${chunk.Page} (PDF 1):`
                        : "(PDF 1):"}{" "}
                  </b>
                  {chunk.Content.replace(/\[Page\s*Unknown\]/gi, "").substring(0, 100)}...
                  {expandedChunk === `pdf1-${index}` && (
                    <Typography variant="body2" style={{ whiteSpace: "pre-line", color: "black", marginTop: "5px" }}>
                      {chunk.Content}
                    </Typography>
                  )}
                </li>
              ))}

              {comparisonSources.pdf2.map((chunk, index) => (
                <li
                  key={`pdf2-${index}`}
                  onClick={() => handleChunkClick(`pdf2-${index}`)}
                  style={{
                    cursor: "pointer",
                    color: "blue",
                    textDecoration: "underline",
                    marginBottom: "5px",
                  }}
                >
                  <b>
                    {chunk.Page && chunk.Page.toLowerCase() !== "unknown"
                        ? `Page ${chunk.Page} (PDF 2):`
                        : "(PDF 2):"}{" "}
                  </b>
                  {chunk.Content.replace(/\[Page\s*\d+\]/gi, "").substring(0, 100)}...
                  {expandedChunk === `pdf2-${index}` && (
                    <Typography variant="body2" style={{ whiteSpace: "pre-line", color: "black", marginTop: "5px" }}>
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

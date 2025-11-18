# Job Application AI Agent
## Natural Language Processing Course Assignment

**Course**: Natural Language Processing  
**Group Members**: [To be filled]
- Member 1: [Name, Student ID]
- Member 2: [Name, Student ID]
- Member 3: [Name, Student ID] (if applicable)

**Submission Date**: November 23, 2024

---

## 1. Background and Significance

### 1.1 Problem Background

The job application process presents significant challenges for millions of job seekers worldwide. The manual process of tailoring CVs for each position is extremely time-consuming, with job seekers spending hours customizing their resumes to match specific job requirements. This challenge is compounded by the difficulty in identifying relevant job opportunities from large job boards, where thousands of listings may contain similar positions with varying terminology and requirements. Additionally, job seekers must prepare for interviews across different companies and roles, each with unique expectations and evaluation criteria. The current system suffers from inefficient matching between candidate skills and job requirements, often relying on simple keyword matching that fails to capture semantic relationships and contextual nuances.

The traditional approach to job applications involves multiple manual steps: searching through job boards, reading job descriptions, identifying relevant opportunities, customizing CVs for each position, and preparing for interviews. Each of these steps requires significant time investment and human effort. The inefficiency is particularly pronounced when job seekers apply to multiple positions, as they must repeat the customization process for each application. This manual process not only consumes valuable time but also introduces inconsistencies and potential errors in application materials.

### 1.2 Significance and Motivation

This project addresses a common problem faced by millions of job seekers globally, offering a solution that can significantly reduce the time and effort required for job applications. The system reduces CV customization time from hours to minutes, enabling job seekers to apply to more positions with higher quality applications. By improving job matching accuracy through semantic understanding, the system helps users discover relevant opportunities that might otherwise be missed through traditional keyword-based searches. Furthermore, the system enhances interview preparation with AI-powered feedback, providing job-specific questions and evaluation that help candidates better prepare for interviews.

The real-world impact of this solution extends beyond individual job seekers. By automating and enhancing the job application process, the system can improve the overall efficiency of the job market, connecting qualified candidates with appropriate positions more effectively. The semantic matching capabilities address a fundamental limitation of current job search platforms, which often miss relevant matches due to terminology differences. For example, a job seeker with "machine learning" experience might miss opportunities listed as "ML engineering" or "deep learning" positions, even though these represent highly relevant matches.

### 1.3 Problem Difficulty

The complexity of this problem stems from several challenging factors. First, processing unstructured documents requires handling CVs in various formats (PDF, DOCX, HTML, plain text) with inconsistent structures, section ordering, and naming conventions. Each CV may present information differently, making automated extraction and understanding a non-trivial task. Second, understanding semantic relationships between CVs and job descriptions goes beyond simple keyword matching, requiring deep comprehension of context, synonyms, and related concepts. For instance, recognizing that "Python programming" and "Python development" represent similar skills, or that "team leadership" and "managing cross-functional teams" describe equivalent experiences.

Third, generating contextually appropriate and personalized content requires understanding both the job requirements and the candidate's background, then synthesizing this information into coherent, professional documents. Fourth, coordinating multiple NLP components in an integrated system presents architectural and technical challenges, requiring careful design to ensure seamless data flow and component interaction. Fifth, managing multi-step AI agent workflows with autonomous decision-making introduces complexity in state management, error handling, and workflow control. Finally, ensuring proper formatting of outputs for CVs and resumes requires attention to professional presentation standards, PDF compatibility, and visual consistency.

---

## 2. Literature Review

### 2.1 Resume/CV Parsing and Information Extraction

The task of extracting structured information from resumes and CVs has been addressed through various approaches in the literature. Traditional methods relied on rule-based parsing, template matching, and structured format extraction. These approaches, while effective for standardized formats, proved fragile when faced with format variations and required manual template creation for each document type. Early work on structured document parsing demonstrated the limitations of these approaches, particularly their inability to handle the diversity of CV formats encountered in practice.

Machine learning approaches introduced Named Entity Recognition (NER) for extracting structured information from CVs. Sequence labeling models using BIO (Beginning-Inside-Outside) tagging were developed to identify CV sections such as personal information, work experience, education, and skills. These approaches showed improved robustness compared to rule-based methods, but still required labeled training data and struggled with highly unstructured formats.

Recent advances have explored using Large Language Models (LLMs) for document understanding, leveraging zero-shot and few-shot learning capabilities for information extraction. GPT-based document parsing studies and instruction-following LLMs have demonstrated format-agnostic parsing capabilities that can handle unstructured documents effectively. These approaches offer significant advantages over traditional methods, as they can adapt to various formats without requiring extensive training data or manual template creation.

The challenges in CV processing include format diversity (PDF, DOCX, HTML, plain text variations), structural inconsistency (different section ordering and naming conventions), multilingual support, and balancing information extraction accuracy between precision and recall. These challenges have motivated the development of more flexible and robust parsing approaches.

### 2.2 Job Matching and Semantic Search

Traditional job matching methods have primarily relied on keyword-based approaches, including TF-IDF, BM25, and exact keyword matching. While these methods have been foundational in information retrieval, they suffer from significant limitations: they miss semantic relationships and struggle with synonym handling. For example, a job requiring "machine learning" expertise might not match a candidate's CV that mentions "ML" or "deep learning," even though these represent highly relevant skills.

Rule-based systems have attempted to address these limitations through skill taxonomy matching, experience level matching, and industry-specific matching rules. However, these approaches require extensive domain expertise to develop and maintain, and they struggle to adapt to evolving job market terminology and requirements.

The development of semantic matching through embeddings has revolutionized text similarity and matching tasks. Word embeddings such as Word2Vec (Mikolov et al., 2013) and GloVe (Pennington et al., 2014) provided semantic representations that captured relationships between words. Sentence embeddings, particularly Sentence-BERT (Reimers & Gurevych, 2019) and Universal Sentence Encoder (Cer et al., 2018), extended this capability to sentence-level semantics, enabling better semantic understanding and context handling.

Vector similarity search using cosine similarity and dot product has become a standard approach for matching, with vector databases such as FAISS and Qdrant enabling efficient similarity search at scale. Academic studies have explored improving job-candidate matching accuracy, using evaluation metrics such as precision, recall, and NDCG (Normalized Discounted Cumulative Gain) for ranking. Industry applications, including LinkedIn's job matching and Indeed's matching algorithms, have demonstrated the practical value of semantic matching approaches, though specific implementation details remain proprietary.

### 2.3 AI Agents and Multi-Step Reasoning

The development of AI agents capable of autonomous reasoning and decision-making has been a significant focus of recent research. The ReAct framework (Yao et al., 2022) introduced reasoning and acting in language models, combining reasoning traces with task-specific actions to enable autonomous decision-making in LLMs. This framework demonstrated how LLMs could be guided to perform complex tasks through explicit reasoning steps.

Chain-of-Thought prompting (Wei et al., 2022) showed that step-by-step reasoning significantly improves LLM performance on multi-step problems. By breaking down complex tasks into sequential reasoning steps, this approach enables LLMs to handle tasks that require multiple logical steps and intermediate reasoning.

Self-consistency and self-refinement techniques have further advanced agent capabilities. Self-consistency decoding (Wang et al., 2022) improves reliability by generating multiple reasoning paths and selecting the most consistent answer. Self-refinement through iterative improvement (Madaan et al., 2023) enables agents to evaluate and improve their own outputs, creating feedback loops that enhance quality.

Autonomous agent systems such as AutoGPT and BabyAGI have demonstrated goal-oriented behavior with multi-step planning and execution. Research on multi-agent systems has explored agent coordination and state management for complex tasks. These developments have shown the potential for autonomous agents to handle complex, multi-step workflows with minimal human intervention.

Validation and quality control in agents have been addressed through self-evaluation techniques, where LLMs evaluate their own outputs, providing quality scores and confidence estimation. Iterative refinement approaches use feedback loops to improve generated content, with early stopping conditions and convergence criteria to optimize the refinement process.

### 2.4 Text Generation and Document Creation

LLM-based text generation has been extensively studied, with prompt engineering techniques (Brown et al., 2020) demonstrating how carefully designed prompts can guide LLM outputs effectively. Few-shot learning and in-context learning have shown that providing examples in prompts enables task-specific behavior without fine-tuning. GPT-3 and instruction-following models have demonstrated the power of these approaches for various text generation tasks.

Structured output generation has been addressed through JSON mode, constrained generation, and template-based approaches. These techniques enable LLMs to generate content in specific formats required by applications. Format-specific generation, including HTML/CSS generation with LLMs, has been explored for document formatting and layout generation.

Personalized content generation has incorporated user context and job requirements to create tailored content. Research on automated resume creation has explored ATS-optimized resume generation, comparing template-based and free-form generation approaches. These studies have shown the importance of context-aware generation for creating relevant and personalized documents.

### 2.5 Interview Preparation and Question Generation

Automatic question generation from text has been studied extensively, with research on generating questions from text (Du et al., 2017) showing applications in educational question generation. Interview question generation from job descriptions represents a specialized application of this research, requiring context-aware question generation that produces domain-specific and personalized question sets based on candidate profiles.

Automated answer scoring has been explored through NLP-based answer evaluation, using semantic similarity for answer matching. Research on automated essay scoring and answer evaluation systems has informed approaches to evaluating interview answers. Feedback generation techniques have been developed to provide constructive feedback and improvement suggestions using NLP.

### 2.6 Query Enhancement and Semantic Search

Query expansion techniques have evolved from traditional methods such as thesaurus-based expansion and synonym replacement to more sophisticated approaches. Pseudo-relevance feedback has been used to improve search queries based on initial results. Recent work has explored LLM-based query expansion, using LLMs to generate query variations and enhance semantic query understanding.

Semantic search systems have leveraged dense retrieval with embeddings, with hybrid search approaches combining keyword and semantic matching. Dense passage retrieval (Karpukhin et al., 2020) has demonstrated the effectiveness of embedding-based search for finding relevant documents.

### 2.7 Integration of NLP Components

Multi-component NLP systems have been designed using pipeline architectures that combine multiple NLP components for end-to-end systems handling complex tasks. Service-oriented NLP approaches have used microservices for NLP tasks, enabling API-based NLP service integration. Production NLP systems have addressed scalability and performance through efficient NLP processing at scale, caching, and optimization techniques. Error handling and reliability have been addressed through robustness in production NLP systems, with fallback mechanisms and error recovery strategies.

### 2.8 Research Gaps and Our Contribution

Despite the extensive research in individual areas, several gaps remain. Most research focuses on individual components (parsing, matching, generation) rather than integrated systems that combine these capabilities. There is limited research on autonomous multi-step CV generation with self-validation, and few systems provide complete job application workflow automation. Additionally, there has been limited exploration of cost-optimized agentic systems for practical applications.

Our project addresses these gaps by providing an integrated NLP platform that combines parsing, matching, generation, and evaluation in one cohesive system. We introduce a novel autonomous CV generation agent with a multi-step agentic workflow featuring self-validation and iterative refinement. Our system demonstrates the practical application of semantic embeddings for job matching and shows the feasibility of agentic workflows using cost-optimized LLM options. Finally, we provide a production-ready system with proper architecture and error handling, demonstrating how these technologies can be integrated into a practical, usable application.

---

## 3. Approach: How NLP and AI Agent Technologies Solve the Problem

### 3.1 Overall Solution Strategy

Our approach integrates multiple NLP techniques to automate and enhance each stage of the job application process. The core strategy involves leveraging state-of-the-art NLP technologies—including information extraction, semantic embeddings, text generation, and multi-step reasoning—to create an intelligent system that understands, processes, and generates job application materials. The key innovation of our system is a multi-step AI agent workflow that autonomously analyzes, generates, and refines CV content, reducing human effort from hours to minutes while maintaining high quality standards.

The system operates on the principle that each stage of the job application process can benefit from specialized NLP techniques. CV parsing uses LLM-based understanding to extract structured information regardless of format. Job matching employs semantic embeddings to find relevant opportunities beyond keyword matching. CV generation leverages an autonomous AI agent that reasons through multiple steps to create tailored content. Interview preparation uses context-aware text generation to produce job-specific questions and evaluations.

### 3.2 NLP Technologies Applied

#### 3.2.1 Information Extraction from Unstructured Documents

CVs present a significant challenge for information extraction due to their diverse formats and inconsistent structures. Our solution addresses this by using LLM-based parsing to extract structured information regardless of format. The system applies Named Entity Recognition implicitly through the LLM's understanding capabilities, identifying key entities such as names, dates, organizations, and skills. The extracted information is transformed into structured JSON format containing personal information, work experience, education, and skills.

This approach offers several advantages over traditional parsing methods. First, it is format-agnostic, handling PDF, DOCX, and other formats without requiring format-specific parsers. Second, it can understand context and relationships between pieces of information, such as associating dates with work experiences or skills with specific roles. Third, it adapts to variations in CV structure and terminology without requiring manual template creation or extensive training data.

#### 3.2.2 Semantic Matching Using Vector Embeddings

Traditional keyword matching fails to capture semantic relationships between CVs and job descriptions. For example, a job requiring "machine learning" expertise might not match a CV mentioning "ML" or "deep learning," even though these represent highly relevant skills. Our solution addresses this by generating semantic embeddings using SentenceTransformer models, which capture the meaning of text beyond exact word matches.

The matching process involves several steps. First, text preprocessing using spaCy extracts noun chunks and normalizes text, identifying key phrases and concepts. Then, the SentenceTransformer model generates embeddings that represent the semantic content of both the CV and job description. Finally, cosine similarity computation between these embeddings provides a match score that reflects semantic similarity rather than just keyword overlap. This approach enables the system to find relevant jobs based on meaning, not just keywords, significantly improving match quality.

#### 3.2.3 AI Agent for Autonomous CV Generation

Generating tailored CVs requires understanding job requirements, analyzing existing CV content, and creating personalized content that highlights relevant experiences and skills. Our AI agent solution addresses this through a multi-step reasoning workflow with autonomous decision-making. Each step uses an LLM to analyze, reason, and generate content, with the agent making decisions about what information to emphasize, how to structure the CV, and when refinement is needed.

The agent features self-validation and iterative refinement capabilities, enabling it to evaluate its own output quality and improve it through feedback loops. The autonomous quality assessment allows the agent to determine whether the generated CV meets quality standards and identifies areas for improvement. This autonomous operation reduces the need for human intervention while ensuring high-quality output.

#### 3.2.4 Context-Aware Text Generation

Interview questions and CV content must be contextually relevant to specific job requirements. Generic content fails to address the unique aspects of each position and company. Our NLP solution addresses this through LLM-based generation with job context as input. The system uses prompt engineering to guide the LLM to produce structured, relevant outputs that align with job requirements.

The generation process incorporates multiple dimensions of context: the job description, the candidate's background, industry standards, and professional best practices. Multi-dimensional evaluation using NLP techniques ensures that generated content meets quality standards across various criteria, including relevance, professionalism, completeness, and accuracy.

#### 3.2.5 Query Enhancement for Semantic Search

Simple keyword searches miss relevant jobs that use different terminology or phrasing. Our solution enhances search queries through LLM-based query expansion, generating synonyms and related terms that capture the semantic intent of the original query. This expanded query is then used with vector search for semantic matching, improving search result relevance through NLP techniques.

The query enhancement process understands the user's intent and expands it to include related concepts, synonyms, and alternative phrasings. For example, a search for "software engineer" might be expanded to include "software developer," "programmer," "application developer," and related terms. This expansion, combined with semantic matching, significantly improves the discovery of relevant job opportunities.

### 3.3 How the System Works in Application Scenario

#### 3.3.1 End-to-End Workflow

The system operates through a streamlined four-step workflow that guides users from CV upload to interview preparation. First, when a user uploads their CV, NLP extracts structured information automatically, parsing the document regardless of format and organizing the content into a structured format. Second, when the user searches for jobs, NLP enhances the query and performs semantic matching, finding relevant opportunities based on meaning rather than just keywords.

Third, when the user selects a job, the AI agent analyzes both the job description and the user's CV, then generates a tailored CV that highlights relevant experiences and skills. The agent operates autonomously through multiple reasoning steps, making decisions about content emphasis, structure, and presentation. Fourth, when the user prepares for an interview, NLP generates job-specific questions and evaluates answers, providing feedback to help improve interview performance.

#### 3.3.2 Key NLP-Driven Features

The system's capabilities are driven by several key NLP features. Intelligent CV parsing handles any CV format through LLM understanding, eliminating the need for format-specific parsers or manual data entry. Semantic job matching finds relevant jobs based on meaning, not just keywords, discovering opportunities that traditional search methods might miss. Autonomous CV tailoring enables the AI agent to independently create personalized CVs, reducing human effort while maintaining quality. Contextual interview preparation generates job-specific questions and feedback, helping users prepare more effectively for interviews.

---

## 4. Implementation Plan

### 4.1 Software Architecture Design

#### 4.1.1 System Architecture Overview

The system follows a full-stack application architecture with a layered design that separates concerns and enables scalability. The architecture pattern employs a three-tier structure: presentation layer (frontend), application layer (backend API), and data layer (databases). This separation allows each component to be developed, tested, and scaled independently while maintaining clear interfaces between layers.

The technology stack is carefully selected to support the NLP and AI agent requirements. The frontend uses React with TypeScript to provide a modern, responsive user interface. The backend employs FastAPI (Python) as a RESTful API layer, chosen for its performance, automatic API documentation, and strong typing support. The database layer uses PostgreSQL with the pgvector extension for structured data storage and vector operations, while Qdrant serves as a dedicated vector database for semantic search and embeddings. LLM integration supports both OpenRouter API for commercial models and Ollama for local, cost-effective open-source models.

#### 4.1.2 Component Architecture

The component architecture follows a layered design with clear separation of responsibilities. The user interface layer (React Frontend) handles user interactions and displays information. The API layer (FastAPI) manages authentication, authorization, request routing, and validation. The service layer contains the core business logic, including CV parsing, job matching, agentic CV generation, interview services, and job search capabilities. The data layer manages both structured data (PostgreSQL) and vector embeddings (Qdrant).

This architecture enables modular development, where each service can be developed and tested independently. The clear interfaces between layers facilitate maintenance and future enhancements. The separation also allows for horizontal scaling, where individual services can be scaled based on demand.

#### 4.1.3 Key Components and Responsibilities

The frontend components provide user-facing functionality. The DashboardPage displays the main user interface, showing CVs, job matches, and application status. The JobsPage provides job browsing and search interface with semantic matching capabilities. The TailoredCVPage offers the CV generation interface with progress tracking, allowing users to see the agent's work in real-time. The InterviewPrepPage provides interview preparation functionality, and the CVEditor enables CV editing and management.

The backend API endpoints handle specific functional areas. The auth.py module manages user authentication and authorization. The cv.py endpoint handles CV upload, parsing, and management. The jobs.py endpoint provides job listing and search functionality. The matches.py endpoint handles job matching and scoring. The interview.py endpoint manages interview question generation and evaluation, while applications.py tracks application status.

The service layer implements the core NLP and AI functionality. The cv/parser_service.py handles CV parsing with LLM, extracting structured information from various formats. The cv/agentic_cv_service.py implements the multi-step CV generation agent workflow. The score_match_service.py performs semantic matching with embeddings. The interview_service.py generates interview questions and evaluates answers. The jobs-finder module provides vector search and query enhancement capabilities.

Data models are organized across two databases. PostgreSQL stores structured relational data including users, CVs, jobs, and applications. Qdrant stores vector embeddings for semantic search, enabling efficient similarity matching between job descriptions and CV content.

#### 4.1.4 Data Flow Overview

The system processes data through several key flows. The CV parsing flow begins with PDF/DOCX upload, extracts text, uses LLM parsing to structure the information, and stores the result in the database. The job matching flow combines CV and job description data, applies spaCy preprocessing, generates embeddings, computes cosine similarity, and produces a match score. The CV generation flow takes job description and CV data, processes them through the AI agent workflow (six steps), and produces a tailored CV. The interview flow uses job context to generate questions via LLM, evaluates answers through LLM analysis, and provides feedback to users.

### 4.2 AI Agent Design

#### 4.2.1 Agentic CV Generation Agent Architecture

The agent is designed as a multi-step reasoning agent with autonomous decision-making capabilities. The agent type enables independent operation, where the agent analyzes, reasons, and generates content without requiring human intervention at each step. This autonomous operation is crucial for creating a system that can handle the complexity of CV generation while maintaining efficiency.

The core design principles guide the agent's behavior. Autonomous operation ensures the agent independently analyzes, reasons, and generates content, making decisions about what information to include and how to present it. Self-validation enables the agent to evaluate its own output quality, identifying issues and areas for improvement. Iterative refinement allows the agent to improve output through feedback loops, continuously enhancing quality until standards are met. Transparency ensures each step is logged and visible to users, providing insight into the agent's reasoning process.

#### 4.2.2 Agent Workflow Design

The agent operates through a six-step autonomous workflow that systematically processes the CV generation task. Step 1 involves job requirement analysis, where the agent receives the job description as input and uses an LLM to analyze job requirements, extracting key skills, responsibilities, and qualifications. The output is a structured analysis of job requirements that guides subsequent steps.

Step 2 performs CV content analysis, where the agent receives the user's existing CV data and uses an LLM to analyze the CV content, identifying relevant experiences, skills, and achievements. The output is a structured analysis of CV strengths and alignment with job requirements. Step 3 creates a tailoring strategy by combining the job analysis and CV analysis. The agent uses an LLM to create a personalized strategy for tailoring the CV to the job, producing detailed recommendations for content emphasis and structure.

Step 4 generates the HTML CV by taking the strategy and original CV data as input. The agent uses an LLM to generate a complete HTML-formatted CV following the strategy, producing a tailored CV ready for review. Step 5 performs output validation, where the agent receives the generated CV and job requirements, uses an LLM to validate CV quality and check alignment with job requirements, and produces a quality score (1-10) along with a list of issues and improvements.

Step 6 implements iterative refinement conditionally. If the quality score is below 8, issues are found, and iterations are below 5, the agent refines the CV based on validation feedback. The process loops back to Step 4 with a refined strategy. The workflow terminates when the quality score reaches 8 or above, no issues are found, or the maximum number of iterations is reached.

#### 4.2.3 Agent Decision-Making Logic

The agent makes several autonomous decisions throughout the workflow. Quality assessment involves the agent deciding whether the CV meets the quality threshold (score ≥ 8), evaluating multiple dimensions including content relevance, professional presentation, and alignment with job requirements. Refinement necessity is determined by the agent based on identified issues, deciding whether improvements are needed and what aspects should be addressed.

Iteration control is managed by the agent, which tracks iterations and stops when conditions are met, preventing infinite loops and optimizing resource usage. Strategy adaptation allows the agent to adjust its strategy based on validation feedback, learning from previous iterations to improve subsequent attempts.

State management tracks the current step in the workflow, maintains history of generated content and validations, stores refinement iterations and improvements, and manages quality scores and issue lists. This state management enables the agent to make informed decisions and provides transparency into the agent's reasoning process.

#### 4.2.4 Agent Implementation Details

LLM integration uses OpenRouter API or Ollama for LLM calls, providing flexibility in model selection and cost optimization. Each step uses carefully engineered prompts that provide clear instructions and context. Structured output parsing uses JSON mode when available, with regex fallback for reliability. Error handling includes retry logic to manage transient failures and ensure robust operation.

Prompt engineering employs step-specific prompts with clear instructions, context passing between steps, output format specifications using JSON schemas, and quality criteria with evaluation rubrics. This careful prompt design ensures consistent, high-quality outputs from the LLM at each step.

Validation and quality control implement multi-dimensional quality assessment, issue detection and categorization, improvement suggestion generation, and early stopping conditions to optimize cost and time. The validation process evaluates multiple aspects of the generated CV, including content quality, formatting, and alignment with requirements.

HTML formatting and sanitization ensure professional output. HTML template loading provides formatting guidance to the LLM. An HTML sanitization pipeline extracts and cleans LLM-generated HTML, removing markdown code blocks and explanatory text. HTML validity checking ensures proper structure, and page margin normalization ensures consistent PDF rendering. Formatting validation is integrated into Step 5 (Output Validation) to catch and address formatting issues.

### 4.3 Deep Model Data Engineering and Training Method Design

#### 4.3.1 Pre-trained Models Used

This project primarily uses pre-trained models rather than training custom deep models from scratch. This approach leverages the extensive knowledge and capabilities of existing models while focusing development effort on integration and application rather than model training. The following sections explain the model selection and usage rationale.

#### 4.3.2 Embedding Model: SentenceTransformer

The system uses the `all-MiniLM-L6-v2` SentenceTransformer model for semantic embeddings. The selection rationale considers several factors. The model is pre-trained on large text corpora, providing strong semantic understanding capabilities. It is optimized for sentence-level embeddings, making it well-suited for matching CVs and job descriptions. The model offers a good balance between accuracy and inference speed, with 384-dimensional embeddings that are suitable for our use case while maintaining computational efficiency.

Data engineering for embeddings involves a text preprocessing pipeline. First, text is extracted from CVs and job descriptions. Second, noun chunk extraction using spaCy identifies key phrases and concepts. Third, text normalization handles lowercasing and special character handling. Fourth, keyword deduplication removes redundant information. Fifth, context combination merges title, responsibilities, and requirements to create rich context for embedding generation.

Embedding generation takes preprocessed text as input, processes it through the SentenceTransformer model to generate a 384-dimensional vector, and outputs a normalized embedding vector for similarity computation. The model is used as-is, leveraging pre-trained semantic understanding without requiring additional training.

#### 4.3.3 LLM Models: OpenRouter/Ollama

The system uses various LLMs through OpenRouter API or local Ollama (GPT-OSS) for different tasks. The usage pattern employs zero-shot learning, where LLMs are used without fine-tuning, relying on their pre-trained capabilities. Prompt engineering guides model behavior through carefully designed prompts. In-context learning provides context in prompts to enable task-specific behavior. Cost optimization is achieved through GPT-OSS models via Ollama, providing a very low-cost alternative that makes agentic workflows with multiple LLM calls economically feasible.

Data engineering for LLM inputs varies by task. For CV parsing, the input is raw CV text extracted from PDF/DOCX, the prompt provides structured extraction instructions with JSON schema, and the output is structured JSON with CV information. For CV generation, the input combines job description, CV data, and strategy, the prompt provides generation instructions with format specifications, and the output is an HTML-formatted CV. For job matching, the input combines CV text and job description, the prompt provides analysis and matching instructions, and the output is a match score and reasoning.

The LLMs are used as pre-trained models with prompt engineering, without requiring additional training or fine-tuning.

#### 4.3.4 Why No Custom Model Training?

Several factors justify the decision to use pre-trained models rather than training custom models. First, pre-trained models are sufficient for our tasks, with existing models (SentenceTransformer, LLMs) providing excellent performance that meets our requirements. Second, we have limited training data, lacking large labeled datasets for CV parsing or job matching that would be necessary for effective custom model training.

Third, cost and time considerations make custom model training impractical. Training custom models would require significant computational resources and time, which would exceed project constraints. Fourth, our focus is on integration rather than model development. The project emphasizes integrating NLP components into a cohesive system rather than developing new models. Fifth, using pre-trained models represents standard industry practice for such applications, as most production NLP systems leverage pre-trained models with task-specific adaptations.

If training were needed, alternative approaches could include fine-tuning LLMs on CV/job description pairs if large datasets were available, training custom embeddings on job-related text corpus, or using supervised learning to train classifiers for job matching if labeled data were available. However, our current approach leverages pre-trained models' general knowledge through effective prompt engineering and preprocessing, achieving excellent results without the overhead of custom training.

---

## 5. Key Technical Challenges and Solutions

### 5.1 Document Parsing: Handling Diverse CV Formats

One of the primary challenges in building the system was handling the diverse formats in which CVs are submitted. CVs come in various formats (PDF, DOCX) with inconsistent structures, making automated parsing difficult. Our solution addresses this through a multi-layered approach. We implement separate extraction methods for PDF (using PyMuPDF) and DOCX (using python-docx) to handle format-specific extraction requirements. Then, we use LLM-based parsing to extract structured data regardless of format, leveraging the LLM's understanding capabilities to handle structural variations. Comprehensive prompt templates with JSON schema validation ensure consistent output format and data quality.

This approach provides several advantages. The format-specific extraction handles the technical aspects of reading different file types, while the LLM-based parsing handles the semantic understanding of content regardless of structure. The JSON schema validation ensures that extracted data meets quality standards and can be reliably processed by downstream components.

### 5.2 LLM Integration: Reliability and Cost Management

External API calls can fail due to network issues, rate limits, or service outages. Additionally, agentic workflows require multiple LLM calls (six or more steps), which can be costly and time-consuming. Our solution addresses these challenges through several mechanisms. Error handling with retry logic and exponential backoff manages transient failures, ensuring robust operation even when individual calls fail. Early stopping conditions (quality threshold, maximum of five refinement rounds) prevent excessive LLM usage when quality standards are met or further improvement is unlikely.

JSON mode and regex fallback for response parsing ensure that we can extract structured data even when the LLM output format varies. Prompt optimization reduces token usage, lowering costs while maintaining quality. Most importantly, support for GPT-OSS (open-source models via Ollama) provides a very low-cost alternative to commercial LLM APIs, enabling cost-effective agentic workflows with multiple LLM calls. This cost optimization makes the system economically viable for practical applications.

### 5.3 Semantic Matching: Embedding Quality and Performance

Balancing accuracy and speed for semantic matching presents a challenge. More accurate models may be slower, while faster models may sacrifice accuracy. Our solution addresses this by selecting `all-MiniLM-L6-v2` for optimal balance, providing good accuracy with fast inference. spaCy preprocessing (noun chunk extraction, normalization) improves embedding quality by focusing on key phrases and concepts. Combining multiple text fields (title, responsibilities, requirements) creates richer context for matching. The Qdrant vector database enables efficient similarity search at scale, supporting real-time matching even with large job databases.

This approach ensures that the system can provide fast, accurate job matching while maintaining scalability. The preprocessing improves match quality by focusing on semantically meaningful content, while the vector database ensures that matching remains fast even as the job database grows.

### 5.4 Agentic Workflow: Multi-Step Coordination

Managing autonomous multi-step workflows with proper termination presents significant challenges. The agent must progress through multiple steps, make decisions at each stage, and know when to stop. Our solution addresses this through a clear step-by-step workflow with defined inputs and outputs for each step, ensuring predictable behavior. State management and validation at each step track progress and ensure data quality. Maximum iteration limits and quality-based stopping conditions prevent infinite loops and optimize resource usage. Progress tracking provides user feedback, showing the agent's work in real-time.

This design ensures that the agent operates reliably and predictably while maintaining autonomy. The clear workflow structure makes the agent's behavior understandable and debuggable, while the stopping conditions ensure efficient operation.

### 5.5 Agentic CV Generation: HTML Formatting Challenges

#### 5.5.1 Challenge: LLM-Generated HTML Structure and Validity

LLMs may generate invalid HTML syntax, including unclosed tags and malformed structure. They may also produce markdown code blocks instead of raw HTML, include explanatory text mixed with HTML content, or generate incomplete HTML documents missing required tags. Additionally, formatting may be inconsistent across different generation attempts.

#### 5.5.2 Challenge: PDF-Ready Formatting Requirements

CVs must be formatted for PDF conversion, requiring proper A4 page dimensions and margins, consistent CSS styling with inline styles for PDF compatibility, one-page layout optimization, professional typography and spacing, and cross-browser and PDF renderer compatibility.

#### 5.5.3 Challenge: Formatting Consistency Across Refinement Iterations

During iterative refinement, formatting may degrade with each refinement round. The LLM may introduce new formatting issues while fixing content, style inconsistencies may emerge between sections, and page margins and layout may shift.

#### 5.5.4 Solutions Implemented

We implemented a comprehensive solution addressing these challenges. HTML template guidance loads a reference HTML template and includes it in the LLM prompt, providing visual structure and formatting examples. An HTML sanitization pipeline removes markdown code block markers, extracts only valid HTML content, removes explanatory text and non-HTML content, ensures proper HTML document structure, and normalizes whitespace.

HTML validity checking quickly validates that output contains HTML structure, checks for required declarations and tags, and prevents invalid content from propagating. Page margin normalization standardizes CSS rules for consistent PDF rendering, ensures A4 page dimensions with appropriate margins, and applies consistent page break handling.

Multi-dimensional validation in Step 5 checks HTML validity and required sections (structural validation), verifies professional appearance, alignment, spacing, and typography (style validation), ensures one-page format and PDF readiness (format validation), and validates that formatting supports content presentation (content-format alignment).

Iterative refinement with formatting preservation explicitly instructs the LLM to maintain HTML structure, includes formatting issues in validation feedback, re-applies sanitization and normalization in each refinement round, and tracks formatting issues systematically. Prompt engineering for formatting explicitly requests a self-contained HTML document with inline CSS, includes template HTML in the prompt, emphasizes HTML/CSS development expertise in the system prompt, and uses low temperature (0.01) for consistent formatting.

The result is a system that reliably produces valid, well-formatted HTML CVs that convert cleanly to PDF, with formatting issues automatically detected and corrected through the agentic validation and refinement process.

---

## 6. Results and Achievements

### 6.1 Functional Capabilities

The system successfully implements all planned functional capabilities. CV parsing extracts structured data from PDF/DOCX CVs with high accuracy, handling diverse formats and structures. Semantic job matching provides relevant job recommendations through vector-based matching that understands semantic relationships. Agentic CV generation creates tailored CVs through an autonomous multi-step workflow that analyzes, generates, and refines content. Interview preparation generates context-aware questions and evaluates answers, providing personalized feedback. Query enhancement optimizes search queries through LLM-based expansion, improving job discovery.

These capabilities work together to provide a complete job application solution, automating tasks that previously required hours of manual effort and reducing them to minutes of automated processing.

### 6.2 NLP Techniques Successfully Applied

The project successfully applies multiple NLP techniques. Information extraction uses LLM-based parsing to extract structured information from unstructured documents. Semantic embeddings employ SentenceTransformer for text vectorization and similarity matching, enabling semantic understanding beyond keyword matching. Text preprocessing uses spaCy for noun chunk extraction and normalization, improving embedding quality. Text generation leverages LLM-based content generation with prompt engineering to create contextually appropriate content. Multi-step reasoning implements an autonomous AI agent workflow with self-validation, enabling complex reasoning tasks. Query optimization uses LLM-based query expansion for semantic search, improving search result relevance.

The successful integration of these techniques demonstrates the practical value of combining multiple NLP approaches to solve complex real-world problems.

### 6.3 System Performance

The system demonstrates strong performance across key metrics. It handles diverse CV formats through LLM understanding, eliminating format-specific limitations. Semantic matching provides relevant job recommendations that traditional keyword-based systems would miss. The agentic workflow produces professional, tailored CVs that meet quality standards. The full-stack implementation with modern architecture ensures scalability, maintainability, and reliability.

The system's performance validates the approach of integrating multiple NLP techniques into a cohesive system, demonstrating that such integration can provide practical value for real-world applications.

---

## 7. Conclusion

### 7.1 Project Summary

This project successfully demonstrates the practical application of NLP and AI agent technologies in building an intelligent job application system. The system integrates multiple NLP techniques—information extraction, semantic embeddings, text generation, and multi-step reasoning—to automate and enhance the job application process. By combining these technologies in a cohesive system, we have created a solution that addresses real-world challenges faced by job seekers.

The project shows that modern NLP technologies, when properly integrated, can provide significant value for practical applications. The autonomous AI agent workflow demonstrates that complex reasoning tasks can be automated while maintaining quality standards. The semantic matching capabilities show how embeddings can improve search and matching beyond traditional keyword-based approaches.

### 7.2 Key Contributions

The project makes several key contributions. First, we successfully integrated multiple NLP components (parsing, matching, generation, evaluation) into a cohesive system, demonstrating how different NLP techniques can work together effectively. Second, we implemented an autonomous multi-step reasoning agent with self-validation and iterative refinement, showing that AI agents can handle complex tasks with minimal human intervention. Third, we addressed a practical problem faced by job seekers, demonstrating NLP's value in automation and real-world applications.

These contributions show that NLP technologies are mature enough for practical applications and that integration of multiple techniques can provide comprehensive solutions to complex problems.

### 7.3 Technical Highlights

The project demonstrates several technical achievements. We leveraged pre-trained models (SentenceTransformer, LLMs) effectively through prompt engineering, showing that careful prompt design can achieve excellent results without model training. We implemented semantic matching using vector embeddings for improved job recommendations, demonstrating the practical value of semantic understanding. We designed an autonomous AI agent workflow that independently analyzes, generates, and refines content, showing that complex reasoning can be automated. We created a full-stack system with clean architecture and comprehensive error handling, demonstrating production-ready implementation.

These technical highlights show that modern NLP technologies can be effectively applied to solve real-world problems when combined with proper system design and implementation practices.

### 7.4 Learning Outcomes

The project provided valuable learning experiences. We gained practical experience with state-of-the-art NLP tools and libraries, understanding their capabilities and limitations. We understood challenges and solutions in LLM integration and prompt engineering, learning how to effectively use LLMs for complex tasks. We experienced semantic search and vector database operations, understanding how embeddings enable semantic understanding. We learned to build production-ready NLP systems with proper architecture, understanding the importance of system design for practical applications.

These learning outcomes demonstrate the educational value of the project, showing how hands-on implementation provides deeper understanding than theoretical study alone.

---

## 8. References

### 8.1 Research Papers

Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., ... & Amodei, D. (2020). Language models are few-shot learners. *Advances in neural information processing systems*, 33, 1877-1901.

Cer, D., Yang, Y., Kong, S. Y., Hua, N., Limtiaco, N., John, R. S., ... & Kurzweil, R. (2018). Universal sentence encoder. *arXiv preprint arXiv:1803.11175*.

Du, X., Shao, J., & Cardie, C. (2017). Learning to ask: Neural question generation for reading comprehension. *Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics*, 1342-1352.

Karpukhin, V., Oguz, B., Min, S., Lewis, P., Wu, L., Edunov, S., ... & Yih, W. T. (2020). Dense passage retrieval for open-domain question answering. *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing*, 6769-6781.

Madaan, A., Tandon, N., Gupta, P., Hallinan, S., Gao, L., Wiegreffe, S., ... & Clark, P. (2023). Self-refine: Iterative refinement with self-feedback. *Advances in Neural Information Processing Systems*, 36.

Mikolov, T., Chen, K., Corrado, G., & Dean, J. (2013). Efficient estimation of word representations in vector space. *arXiv preprint arXiv:1301.3781*.

Pennington, J., Socher, R., & Manning, C. D. (2014). GloVe: Global vectors for word representation. *Proceedings of the 2014 conference on empirical methods in natural language processing (EMNLP)*, 1532-1543.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using siamese BERT-networks. *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)*, 3982-3992.

Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., ... & Zhou, D. (2022). Self-consistency improves chain of thought reasoning in language models. *arXiv preprint arXiv:2203.11171*.

Wei, J., Wang, X., Schuurmans, D., Bosma, M., Chi, E., Le, Q., & Zhou, D. (2022). Chain-of-thought prompting elicits reasoning in large language models. *Advances in Neural Information Processing Systems*, 35, 24824-24837.

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). ReAct: Synergizing reasoning and acting in language models. *arXiv preprint arXiv:2210.03629*.

### 8.2 Technologies and Libraries

**Backend**: FastAPI (Python), PostgreSQL + pgvector, Qdrant  
**Frontend**: React + TypeScript  
**NLP Libraries**: spaCy, SentenceTransformers  
**Document Processing**: PyMuPDF, python-docx  
**LLM APIs**: OpenRouter, Ollama

### 8.3 Key Implementation Files

- `backend/services/cv/parser_service.py`: CV parsing with LLM
- `backend/services/cv/agentic_cv_service.py`: Agentic CV generation workflow
- `backend/services/score_match_service.py`: Semantic matching implementation
- `backend/services/interview_service.py`: Interview question generation
- `docs/AGENTIC_CV_GENERATION.md`: Detailed agent workflow documentation

---

**Report Guidelines**:  
- **Length**: Concise and clear (target: 10-15 pages)  
- **Focus**: Clearly explain background, approach, and implementation  
- **Emphasis**: How NLP and AI agent technologies solve the problem

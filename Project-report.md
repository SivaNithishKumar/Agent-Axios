CHAPTER 1 INTRODUCTION 

This chapter provides an overview of the LLM-based framework developed to detect vulnerabilities in open-source software. It combines symbolic code analysis with neural language models to enhance accuracy and contextual understanding in identifying security flaws. The approach aims to create an automated, intelligent, and scalable vulnerability detection system. 

 

BACKGROUND 

In today’s software ecosystem, open-source components form the foundation of countless applications, frameworks, and services. While open-source accelerates innovation, it also introduces significant security risks — as vulnerabilities in widely used libraries can propagate across numerous dependent systems. Traditional security tools such as Static Application Security Testing (SAST), Dynamic Application Security Testing (DAST), and Software Composition Analysis (SCA) have been effective to an extent, but they face limitations when analyzing large, complex, and semantically diverse codebases. These conventional methods often rely on rule-based scanning or pattern matching, which can lead to false positives, false negatives, and limited contextual understanding of code logic. 

In recent years, advances in Artificial Intelligence (AI), particularly Large Language Models (LLMs) like GPT and Code-BERT, have opened new possibilities for understanding and reasoning about source code. Unlike static tools, LLMs can analyze the semantic meaning, code intent, and logical flow of programs, making them capable of detecting subtle or context-dependent vulnerabilities that static analyzers may miss. However, raw LLMs struggle with scalability and context length limitations when dealing with large repositories. 

  

To address these challenges, a hybrid symbolic-neural approach is adopted in this work. Symbolic methods such as Abstract Syntax Tree (AST) parsing and static code pattern matching provide structural accuracy, while LLM-based embeddings and Retrieval-Augmented Generation (RAG) bring semantic depth and contextual awareness. This combination enables the system to detect vulnerabilities more intelligently by understanding both the syntax and semantics of the code. The integration of tools like Tree-sitter, FAISS Vector Database, and Provenance Pruning further optimizes the retrieval and reasoning process, ensuring scalability and precision. 

This framework thus represents a step forward in automated software vulnerability detection - bridging the gap between traditional static analysis and intelligent, context-aware reasoning powered by LLMs, designed to fit seamlessly into modern DevSecOps workflows for real-world applicability. 

 

SOFTWARE SECURITY CHALLENGES IN OPEN-SOURCE ECOSYSTEMS 

 

Open-source ecosystems have become the backbone of modern software development, enabling rapid innovation, cost efficiency, and community-driven progress. However, this openness also introduces significant security concerns. Since open-source projects are publicly accessible and collaboratively maintained, their source code is exposed to both contributors and potential attackers. While this transparency promotes faster bug discovery, it also provides attackers with opportunities to identify and exploit vulnerabilities before they are patched. 

 
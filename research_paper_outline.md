# Research Paper Outline: Hidden Pleiotropy Discovery

## Title Ideas
1. "Shared Biological Hubs: Uncovering Hidden Pleiotropy Across Distinct Human Diseases"
2. "The Genetic Bridges: Cross-Trait Phenotypic Mapping Using GWAS and ClinVar"
3. "Network Pleiotropy: How Single Genes Drive Unrelated Complex Traits"

## 1. Abstract
* **Background:** Biological systems are highly interconnected, yet medical diagnostics often treat diseases as isolated silos (e.g., psychiatry separate from autoimmune). "Pleiotropy" occurs when one gene influences multiple seemingly unrelated traits.
* **The Problem:** Many genes responsible for complex systemic diseases have disjointed research literature because independent medical fields study them in isolation.
* **Objective:** To computationally discover "pleiotropic hub" genes linking highly diverse physiological traits (e.g., neurological vs. cardiovascular) and explain their underlying shared biology using Gene Ontology (GO).
* **Methods/Findings:** [To be populated]

## 2. Introduction
* **Pleiotropy in Human Genetics:** Define pleiotropy and why it complicates drug targeting but provides insight into fundamental biology.
* **GWAS & Trait Silos:** Explain how GWAS uncovers countless associations, but crossing finding across distinct medical domains is under-analyzed.
* **Hypothesis:** We hypothesize that a subset of heavily pleiotropic genes act as universal physiological stress responders or master regulators, bridging distinct disease categories (e.g., metabolic and psychiatric).

## 3. Methods
* **Data Integration:** 
  * Leveraging perfectly mapped (strict NOT NULL) databases combining GWAS Catalog (complex traits) and ClinVar (Mendelian variants).
* **Metric of Pleiotropy:**
  * Define what qualifies a gene as "pleiotropic" (e.g., appearing in >5 unique trait groups, such as cardiovascular, nervous, and metabolic).
* **Functional Explanation:**
  * Using Gene Ontology (GO) terms from our `gene_go_terms` table to characterize the shared pathways (e.g., "inflammatory response") driving the disparate traits.

## 4. Results
* **Identifying the Pleiotropic Hubs:**
  * [Pending: The top genes associated with the most diverse EFO/reported traits]
* **Case Studies:**
  * [Pending: Deep dives into 2-3 specific genes showing exactly which wildly different diseases they connect]

## 5. Discussion
* **Biological Mechanism:** How one GO pathway (e.g., calcium channel regulation) causes two totally different diseases depending on the tissue type.
* **Drug Repurposing:** If a drug treats the metabolic trait of Gene X, could it be repurposed for the psychiatric trait of Gene X?

## Next Steps:
1. [ ] **Pleiotropy Query:** Write a script to find genes in `gene_traits` with the highest number of *distinct* medical traits.
2. [ ] **Semantic Clustering:** Group traits into broad categories (e.g., is "height" too similar to "BMI" to be considered truly pleiotropic compared to "Schizophrenia" and "Crohn's disease"?).
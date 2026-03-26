from src.rag.pipeline import load_graph, build_schema_summary, answer_with_rag, answer_baseline, pretty_print

def run_cli(kb_path: str = "kg_artifacts/full_kb.ttl"):
    print("=== F1 Knowledge Graph RAG Demo ===")
    print("Chargement du KB...")
    
    g      = load_graph(kb_path)
    schema = build_schema_summary(g)
    
    print("KB chargé. Tape 'quit' pour quitter.\n")
    
    while True:
        question = input("Question: ").strip()
        
        if question.lower() == "quit":
            break
        if not question:
            continue
        
        print("\n--- Baseline (sans RAG) ---")
        baseline = answer_baseline(question)
        print(baseline[:300])
        
        print("\n--- RAG (SPARQL + KB) ---")
        result = answer_with_rag(g, schema, question)
        pretty_print(result)
        print()

if __name__ == "__main__":
    run_cli()
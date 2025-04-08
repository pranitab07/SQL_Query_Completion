from retrieve_context import get_similar_context

results = get_similar_context("How do I filter customers by age?")
for r in results:
    print(r["sql_prompt"], "\n→", r["sql"], "\n")
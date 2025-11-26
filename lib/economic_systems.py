"""
Economic system definitions for Thunderclap ideology queries.
Provides clear definitions to ensure consistent understanding of economic systems.
"""

ECONOMIC_SYSTEM_DEFINITIONS = {
    "free market": {
        "definition": "An economic system where prices, production, and distribution are determined by voluntary exchange in markets, with minimal state intervention. Private property rights are central, and economic decisions are decentralized.",
        "state_vs_market": "Market-dominant: prices and allocation determined by supply and demand",
        "key_features": ["Private property rights", "Voluntary exchange", "Price signals", "Competition", "Minimal state regulation"]
    },
    "free-market": {
        "definition": "An economic system where prices, production, and distribution are determined by voluntary exchange in markets, with minimal state intervention. Private property rights are central, and economic decisions are decentralized.",
        "state_vs_market": "Market-dominant: prices and allocation determined by supply and demand",
        "key_features": ["Private property rights", "Voluntary exchange", "Price signals", "Competition", "Minimal state regulation"]
    },
    "command economy": {
        "definition": "An economic system where the state or central authority controls production, distribution, prices, and resource allocation. Economic planning replaces market mechanisms.",
        "state_vs_market": "State-dominant: central planning determines production and allocation",
        "key_features": ["Central planning", "State ownership of means of production", "Price controls", "Production quotas", "Resource allocation by state"]
    },
    "command economies": {
        "definition": "Economic systems where the state or central authority controls production, distribution, prices, and resource allocation. Economic planning replaces market mechanisms.",
        "state_vs_market": "State-dominant: central planning determines production and allocation",
        "key_features": ["Central planning", "State ownership of means of production", "Price controls", "Production quotas", "Resource allocation by state"]
    },
    "socialism": {
        "definition": "An economic system where the means of production, distribution, and exchange are owned or regulated by the community or state. Emphasizes social ownership and democratic control of economic resources.",
        "state_vs_market": "Varies: can range from state-controlled to market-socialist models with social ownership",
        "key_features": ["Social ownership", "Democratic control", "Redistribution", "Public services", "Worker participation"]
    },
    "socialist": {
        "definition": "Relating to socialism: an economic system where the means of production, distribution, and exchange are owned or regulated by the community or state.",
        "state_vs_market": "Varies: can range from state-controlled to market-socialist models with social ownership",
        "key_features": ["Social ownership", "Democratic control", "Redistribution", "Public services", "Worker participation"]
    },
    "marxism": {
        "definition": "A theoretical framework analyzing capitalism through class struggle, predicting transition to socialism and eventually communism. Emphasizes historical materialism and critique of capitalist exploitation.",
        "state_vs_market": "Theoretical: advocates transition from capitalism (market) to socialism/communism (state/communal control)",
        "key_features": ["Class struggle", "Historical materialism", "Critique of capitalism", "Revolutionary transition", "Communal ownership"]
    },
    "marxist": {
        "definition": "Relating to Marxism: a theoretical framework analyzing capitalism through class struggle, predicting transition to socialism and eventually communism.",
        "state_vs_market": "Theoretical: advocates transition from capitalism (market) to socialism/communism (state/communal control)",
        "key_features": ["Class struggle", "Historical materialism", "Critique of capitalism", "Revolutionary transition", "Communal ownership"]
    },
    "communism": {
        "definition": "A theoretical economic system where property is communally owned and each person works and is paid according to their abilities and needs. In practice, often implemented as state-controlled command economies.",
        "state_vs_market": "Theoretical: stateless, classless society with communal ownership. Practical: often state-controlled command economy",
        "key_features": ["Communal ownership", "Classless society", "From each according to ability, to each according to need", "Often implemented as state command economy"]
    },
    "communist": {
        "definition": "Relating to communism: a theoretical economic system where property is communally owned. In practice, often implemented as state-controlled command economies.",
        "state_vs_market": "Theoretical: stateless, classless society with communal ownership. Practical: often state-controlled command economy",
        "key_features": ["Communal ownership", "Classless society", "From each according to ability, to each according to need", "Often implemented as state command economy"]
    },
    "mixed economy": {
        "definition": "An economic system combining elements of market and command economies. Private enterprise coexists with state intervention, regulation, and public ownership of certain sectors.",
        "state_vs_market": "Mixed: market mechanisms operate alongside state regulation, public services, and strategic intervention",
        "key_features": ["Private and public sectors", "Market mechanisms with state regulation", "Public services", "Strategic state intervention", "Social safety nets"]
    },
    "mixed economies": {
        "definition": "Economic systems combining elements of market and command economies. Private enterprise coexists with state intervention, regulation, and public ownership of certain sectors.",
        "state_vs_market": "Mixed: market mechanisms operate alongside state regulation, public services, and strategic intervention",
        "key_features": ["Private and public sectors", "Market mechanisms with state regulation", "Public services", "Strategic state intervention", "Social safety nets"]
    },
    "mixed model": {
        "definition": "An economic system combining elements of market and command economies. Private enterprise coexists with state intervention, regulation, and public ownership of certain sectors.",
        "state_vs_market": "Mixed: market mechanisms operate alongside state regulation, public services, and strategic intervention",
        "key_features": ["Private and public sectors", "Market mechanisms with state regulation", "Public services", "Strategic state intervention", "Social safety nets"]
    },
    "collectivism": {
        "definition": "An economic system emphasizing collective ownership and decision-making over individual ownership. Resources and production are managed collectively.",
        "state_vs_market": "Varies: can be state-controlled or community-based collective ownership",
        "key_features": ["Collective ownership", "Group decision-making", "Shared resources", "Community priorities over individual"]
    },
    "collectivist": {
        "definition": "Relating to collectivism: an economic system emphasizing collective ownership and decision-making over individual ownership.",
        "state_vs_market": "Varies: can be state-controlled or community-based collective ownership",
        "key_features": ["Collective ownership", "Group decision-making", "Shared resources", "Community priorities over individual"]
    }
}

def get_economic_system_definition(term: str) -> dict:
    """
    Get definition for an economic system term.
    
    Args:
        term: Economic system term (e.g., "free market", "socialism")
    
    Returns:
        Dictionary with definition, state_vs_market position, and key features
        Returns None if term not found
    """
    return ECONOMIC_SYSTEM_DEFINITIONS.get(term.lower())

def format_definitions_for_prompt() -> str:
    """
    Format economic system definitions for inclusion in LLM prompts.
    
    Returns:
        Formatted string with definitions
    """
    lines = ["**Economic System Definitions (for reference):**"]
    lines.append("")
    
    for term, info in ECONOMIC_SYSTEM_DEFINITIONS.items():
        # Skip duplicates (e.g., "free-market" vs "free market")
        if term in ["free-market", "command economies", "mixed economies", "socialist", "marxist", "communist", "collectivist"]:
            continue
            
        lines.append(f"- **{term.title()}**: {info['definition']}")
        lines.append(f"  - State vs Market: {info['state_vs_market']}")
        lines.append(f"  - Key Features: {', '.join(info['key_features'])}")
        lines.append("")
    
    return "\n".join(lines)


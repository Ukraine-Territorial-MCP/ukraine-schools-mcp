"""Ukraine Schools MCP with EDBO and KATOTTG."""

from mcp.server.mcpserver import MCPServer
from data_engine.edbo import get_school_info as edbo_info
from data_engine.territories import get_territory

server = MCPServer(name="ukraine-schools-mcp")


@server.tool()
def get_school_info(school_id: int) -> dict:
    """Get school details and administrative territory."""
    school = edbo_info(school_id)

    if not school.get("found"):
        return school

    katottg = school.get("katottg")

    school["territory"] = (
        get_territory(katottg) if katottg else None
    )

    return school



@server.tool()
def list_schools_by_community(community_code: str) -> dict:
    """List educational institutions by Ukrainian KATOTTG community."""
    from data_engine.schools import list_schools
    return list_schools(community_code)




@server.tool()
def get_education_budget(
    budget_code: str,
    year: int = 2026,
) -> dict:
    """Get education budget plans and actual expenses from Open Budget."""
    from data_engine.openbudget import get_education_budget as fetch
    return fetch(budget_code, year)


from mcp.server.transport_security import TransportSecuritySettings

app = server.streamable_http_app(
    transport_security=TransportSecuritySettings(
        allowed_hosts=[
            "mcp.edeputat.com",
            "mcp.edeputat.com:*",
            "localhost:*",
            "127.0.0.1:*",
        ],
        allowed_origins=[
            "https://mcp.edeputat.com",
        ],
    ),

    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)

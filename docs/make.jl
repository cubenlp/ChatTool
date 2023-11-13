using Documenter

makedocs(
    sitename="ChatTool",
    pages=[
        "Home" => "index.md",
        "Getting-Started" => "Getting-Started.md"
    ],
)

# deploydocs(
#     repo = "github.com/CubeNLP/chatapi_toolkit",
#     devurl = "dev",
#     devbranch = "master",
#     versions = ["stable" => "^", "dev" =>  "dev"],
# )
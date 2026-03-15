"""
CLI entry point for the Zscaler MCP Deployer.
"""
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

from . import __version__
from .validators.aws import AWSSessionValidator
from .validators.iam import IAMPermissionValidator
from .validators.zscaler import ZscalerCredentialValidator
from .errors import AWSCredentialsError, AWSRegionError, AWSPermissionsError
from .messages import ErrorMessageCatalog, UserGuidance

app = typer.Typer(
    name="zscaler-mcp-deploy",
    help="Zscaler MCP Deployment Validator and Preflight Checker",
    add_completion=False,
)
console = Console()

def version_callback(value: bool):
    """Callback function to show version and exit."""
    if value:
        typer.echo(f"zscaler-mcp-deploy {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True,
        help="Show version and exit."
    ),
):
    """
    Zscaler MCP Deployer CLI - Validate AWS and Zscaler configurations before deployment.
    """
    pass

@app.command()
def preflight(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive region selection"),
    skip_iam: bool = typer.Option(False, "--skip-iam", help="Skip IAM permission validation"),
    zscaler_cloud: str = typer.Option("zscaler", "--zscaler-cloud", help="Zscaler cloud name"),
    zscaler_username: Optional[str] = typer.Option(None, "--zscaler-username", help="Zscaler username (email)"),
    zscaler_password: Optional[str] = typer.Option(None, "--zscaler-password", help="Zscaler password"),
    zscaler_api_key: Optional[str] = typer.Option(None, "--zscaler-api-key", help="Zscaler API key"),
    skip_zscaler: bool = typer.Option(False, "--skip-zscaler", help="Skip Zscaler credential validation"),
):
    """Run preflight validation checks for AWS and Zscaler configurations."""
    console.print("[bold blue]Zscaler MCP Deployment Preflight Validator[/bold blue]")
    console.print("[yellow]Running validation checks...[/yellow]")
    
    # AWS Validation
    aws_validator = AWSSessionValidator(profile_name=profile, region=region)
    
    # Handle interactive region selection
    target_region = region
    if interactive and not region:
        selected_region = aws_validator.prompt_for_region()
        if selected_region:
            target_region = selected_region
        else:
            console.print("[yellow]Interactive region selection cancelled.[/yellow]")
            raise typer.Exit(0)
    
    is_valid, messages = aws_validator.validate_session(target_region)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Check", style="dim", width=20)
    table.add_column("Status", width=12)
    table.add_column("Details", width=40)
    
    if is_valid:
        table.add_row("AWS Session", "✅ OK", messages[0])
        table.add_row("AWS Region", "✅ OK", messages[1])
        
        # IAM Permission Validation (if not skipped)
        if not skip_iam:
            console.print("[yellow]Checking IAM permissions...[/yellow]")
            iam_validator = IAMPermissionValidator(profile_name=profile, region=target_region)
            try:
                results = iam_validator.validate_required_permissions()
                all_valid = True
                
                # Check each service
                for service, result in results.items():
                    if result['valid']:
                        table.add_row(f"IAM {service.title()}", "✅ OK", f"All required permissions available")
                    else:
                        all_valid = False
                        denied_count = len(result['denied'])
                        table.add_row(f"IAM {service.title()}", "❌ FAILED", f"{denied_count} permissions missing")
                        # Show policy suggestion for first denied action
                        if result['missing_policy']:
                            console.print(f"\n[bold red]Missing policy for {service}:[/bold red]")
                            console.print(f"[cyan]{result['missing_policy']}[/cyan]")
                
                if not all_valid:
                    is_valid = False
            except Exception as e:
                table.add_row("IAM Permissions", "⚠️  ERROR", f"Failed to validate: {str(e)}")
                console.print(f"[red]Warning:[/red] Could not validate IAM permissions: {str(e)}")
        
        # Zscaler Validation (if not skipped)
        if not skip_zscaler:
            console.print("[yellow]Checking Zscaler credentials...[/yellow]")
            zscaler_validator = ZscalerCredentialValidator(
                cloud=zscaler_cloud,
                username=zscaler_username,
                password=zscaler_password,
                api_key=zscaler_api_key
            )
            
            try:
                zscaler_valid, zscaler_messages = zscaler_validator.validate_credentials()
                
                if zscaler_valid:
                    table.add_row("Zscaler Credentials", "✅ OK", "All credentials valid")
                else:
                    # Check if it's a credential format issue or authentication issue
                    table.add_row("Zscaler Credentials", "❌ FAILED", zscaler_messages[-1])
                    is_valid = False
                    
            except Exception as e:
                table.add_row("Zscaler Credentials", "⚠️  ERROR", f"Failed to validate: {str(e)}")
                console.print(f"[red]Warning:[/red] Could not validate Zscaler credentials: {str(e)}")
                is_valid = False
        
        console.print(table)
        
        if is_valid:
            console.print("[green]All checks passed! Ready for deployment.[/green]")
        else:
            console.print("[red]Validation failed. Please fix the issues above before deployment.[/red]")
            raise typer.Exit(code=1)
    else:
        table.add_row("AWS Session", "❌ FAILED", messages[0])
        if len(messages) > 1:
            table.add_row("AWS Region", "❌ FAILED", messages[1])
        console.print(table)
        console.print("[red]Validation failed. Please fix the issues above before deployment.[/red]")
        raise typer.Exit(code=1)

@app.command()
def help_credentials():
    """Show detailed help for configuring AWS and Zscaler credentials."""
    console.print("[bold blue]AWS and Zscaler Credential Configuration Guide[/bold blue]\n")
    
    # AWS Help
    console.print("[bold]AWS Credentials:[/bold]")
    console.print(UserGuidance.get_aws_credential_help())
    console.print("\n" + "="*60 + "\n")
    
    # Zscaler Help
    console.print("[bold]Zscaler Credentials:[/bold]")
    console.print(UserGuidance.get_zscaler_credential_help())
    console.print("\n" + "="*60 + "\n")
    
    # Common Issues
    console.print("[bold]Troubleshooting Common Issues:[/bold]")
    console.print(UserGuidance.get_common_issues_help())

if __name__ == "__main__":
    app()
"""
CLI entry point for the Zscaler MCP Deployer.
"""
import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table

from . import __version__
from .validators.aws import AWSSessionValidator
from .validators.iam import IAMPermissionValidator
from .validators.zscaler import ZscalerCredentialValidator
from .errors import AWSCredentialsError, AWSRegionError, AWSPermissionsError
from .messages import ErrorMessageCatalog, UserGuidance
from .bootstrap import BootstrapOrchestrator
from .deploy import DeployOrchestrator
from .models import BootstrapConfig, DeployConfig

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


@app.command()
def bootstrap(
    secret_name: Optional[str] = typer.Option(None, "--secret-name", "-s", help="Name for the Secrets Manager secret"),
    role_name: Optional[str] = typer.Option(None, "--role-name", "-r", help="Name for the IAM execution role"),
    kms_key_id: Optional[str] = typer.Option(None, "--kms-key-id", "-k", help="KMS key ARN for secret encryption (optional, uses AWS managed key if not specified)"),
    use_existing: bool = typer.Option(False, "--use-existing", help="Allow using existing resources (idempotent behavior)"),
    region: Optional[str] = typer.Option(None, "--region", help="AWS region (optional, uses configured default)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name (optional)"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Zscaler username (email)"),
    password: Optional[str] = typer.Option(None, "--password", help="Zscaler password"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="Zscaler API key (32 hex characters)"),
    cloud: str = typer.Option("zscaler", "--cloud", "-c", help="Zscaler cloud name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description for created resources"),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Fail if required values are missing instead of prompting"),
):
    """Bootstrap AWS resources for Zscaler MCP deployment.
    
    Creates or uses existing:
    - AWS Secrets Manager secret for Zscaler credentials
    - IAM execution role for Bedrock AgentCore
    
    All operations are idempotent - running multiple times is safe.
    """
    console.print("[bold blue]Zscaler MCP Bootstrap[/bold blue]")
    console.print("[dim]Creating AWS resources for Zscaler MCP deployment...[/dim]\n")
    
    # Prompt for missing required values
    if not secret_name:
        if non_interactive:
            console.print("[red]Error:[/red] --secret-name is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        secret_name = typer.prompt("Secret name")
    
    if not role_name:
        if non_interactive:
            console.print("[red]Error:[/red] --role-name is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        role_name = typer.prompt("Role name")
    
    if not username:
        if non_interactive:
            console.print("[red]Error:[/red] --username is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        username = typer.prompt("Zscaler username (email)")
    
    if not password:
        if non_interactive:
            console.print("[red]Error:[/red] --password is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        password = typer.prompt("Zscaler password", hide_input=True)
    
    if not api_key:
        if non_interactive:
            console.print("[red]Error:[/red] --api-key is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        api_key = typer.prompt("Zscaler API key (32 hex characters)", hide_input=True)
    
    # Create bootstrap configuration
    config = BootstrapConfig(
        secret_name=secret_name,
        role_name=role_name,
        username=username,
        password=password,
        api_key=api_key,
        cloud=cloud,
        kms_key_id=kms_key_id,
        region=region,
        profile_name=profile,
        description=description or f"Zscaler MCP resources for {cloud} cloud"
    )
    
    # Initialize orchestrator
    orchestrator = BootstrapOrchestrator(
        region=region,
        profile_name=profile
    )
    
    # Run bootstrap
    try:
        result = orchestrator.bootstrap_resources(config)
        
        # Display results in Rich table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Resource", style="dim", width=20)
        table.add_column("Status", width=15)
        table.add_column("ARN", width=60)
        
        if result.success:
            # Secret row
            secret_status = "[green]Created[/green]" if result.secret_created else "[blue]Reused[/blue]"
            table.add_row("Secret", secret_status, result.secret_arn or "N/A")
            
            # Role row
            role_status = "[green]Created[/green]" if result.role_created else "[blue]Reused[/blue]"
            table.add_row("IAM Role", role_status, result.role_arn or "N/A")
            
            console.print(table)
            console.print("\n[green]✅ Bootstrap completed successfully![/green]")
            console.print("\n[dim]Next steps:[/dim]")
            console.print(f"  1. Secret ARN: [cyan]{result.secret_arn}[/cyan]")
            console.print(f"  2. Role ARN:   [cyan]{result.role_arn}[/cyan]")
            
        else:
            # Failed - show what we have
            if result.secret_arn:
                secret_status = "[green]Created[/green]" if result.secret_created else "[blue]Reused[/blue]"
                table.add_row("Secret", secret_status, result.secret_arn)
            else:
                table.add_row("Secret", "[red]Failed[/red]", "N/A")
            
            if result.role_arn:
                role_status = "[green]Created[/green]" if result.role_created else "[blue]Reused[/blue]"
                table.add_row("IAM Role", role_status, result.role_arn)
            else:
                table.add_row("IAM Role", "[red]Failed[/red]", "N/A")
            
            console.print(table)
            console.print(f"\n[red]❌ Bootstrap failed during '{result.phase}' phase[/red]")
            
            # Display error using S01 error patterns
            console.print(f"\n[bold red]Error {result.error_code}:[/bold red] {result.error_message}")
            
            # Show fix commands based on error code
            if result.error_code:
                if "PreflightFailed" in result.error_code:
                    console.print("\n[blue]Remediation:[/blue] Check your AWS credentials and region configuration")
                    console.print("[green]🔧 Suggested fix commands:[/green]")
                    console.print("   [cyan]$ aws configure[/cyan]")
                    console.print("   [cyan]$ zscaler-mcp-deploy preflight --region us-east-1[/cyan]")
                elif "SecretFailed" in result.error_code:
                    console.print("\n[blue]Remediation:[/blue] Check Secrets Manager permissions and KMS key access")
                    console.print("[green]🔧 Suggested fix commands:[/green]")
                    console.print("   [cyan]$ aws secretsmanager list-secrets[/cyan]")
                    if kms_key_id:
                        console.print("   [cyan]$ aws kms describe-key --key-id {kms_key_id}[/cyan]")
                elif "RoleFailed" in result.error_code:
                    console.print("\n[blue]Remediation:[/blue] Check IAM permissions for role creation")
                    console.print("[green]🔧 Suggested fix commands:[/green]")
                    console.print("   [cyan]$ aws iam list-roles[/cyan]")
                    console.print("   [cyan]$ aws iam get-role --role-name {role_name}[/cyan]")
            
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error:[/red] {str(e)}")
        console.print("\n[blue]Remediation:[/blue] Check the error details and try again")
        console.print("[green]🔧 For detailed help:[/green]")
        console.print("   [cyan]$ zscaler-mcp-deploy bootstrap --help[/cyan]")
        raise typer.Exit(code=1)


@app.command()
def deploy(
    runtime_name: Optional[str] = typer.Option(None, "--runtime-name", "-n", help="Name for the Bedrock runtime"),
    secret_name: Optional[str] = typer.Option(None, "--secret-name", "-s", help="Name for the Secrets Manager secret"),
    role_name: Optional[str] = typer.Option(None, "--role-name", "-r", help="Name for the IAM execution role"),
    image_uri: Optional[str] = typer.Option(None, "--image-uri", "-i", help="Container image URI (optional, uses default if not provided)"),
    enable_write_tools: bool = typer.Option(False, "--enable-write-tools", "-w", help="Enable write-capable MCP tools"),
    kms_key_id: Optional[str] = typer.Option(None, "--kms-key-id", "-k", help="KMS key ARN for secret encryption (optional)"),
    region: Optional[str] = typer.Option(None, "--region", help="AWS region (optional, uses configured default)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name (optional)"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Zscaler username (email)"),
    password: Optional[str] = typer.Option(None, "--password", help="Zscaler password"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="Zscaler API key (32 hex characters)"),
    cloud: str = typer.Option("zscaler", "--cloud", "-c", help="Zscaler cloud name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description for created resources"),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Fail if required values are missing instead of prompting"),
    poll_timeout: int = typer.Option(600, "--poll-timeout", "-t", help="Timeout for runtime polling in seconds (default: 600)"),
):
    """Deploy Zscaler MCP server to AWS Bedrock AgentCore.
    
    Performs complete deployment:
    1. Creates or uses existing Secrets Manager secret for Zscaler credentials
    2. Creates or uses existing IAM execution role for Bedrock
    3. Creates Bedrock AgentCore runtime with the Zscaler MCP server
    4. Polls until runtime reaches READY status
    
    All operations are idempotent - running multiple times is safe.
    On runtime failure, the runtime is rolled back but bootstrap resources are kept.
    """
    console.print("[bold blue]Zscaler MCP Deployment[/bold blue]")
    console.print("[dim]Deploying Zscaler MCP server to AWS Bedrock AgentCore...[/dim]\n")
    
    # Prompt for missing required values
    if not runtime_name:
        if non_interactive:
            console.print("[red]Error:[/red] --runtime-name is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        runtime_name = typer.prompt("Runtime name")
    
    if not secret_name:
        if non_interactive:
            console.print("[red]Error:[/red] --secret-name is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        secret_name = typer.prompt("Secret name")
    
    if not role_name:
        if non_interactive:
            console.print("[red]Error:[/red] --role-name is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        role_name = typer.prompt("Role name")
    
    if not username:
        if non_interactive:
            console.print("[red]Error:[/red] --username is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        username = typer.prompt("Zscaler username (email)")
    
    if not password:
        if non_interactive:
            console.print("[red]Error:[/red] --password is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        password = typer.prompt("Zscaler password", hide_input=True)
    
    if not api_key:
        if non_interactive:
            console.print("[red]Error:[/red] --api-key is required (or remove --non-interactive to prompt)")
            raise typer.Exit(code=1)
        api_key = typer.prompt("Zscaler API key (32 hex characters)", hide_input=True)
    
    # Create deployment configuration
    config = DeployConfig(
        runtime_name=runtime_name,
        secret_name=secret_name,
        role_name=role_name,
        username=username,
        password=password,
        api_key=api_key,
        cloud=cloud,
        image_uri=image_uri,
        enable_write_tools=enable_write_tools,
        kms_key_id=kms_key_id,
        region=region,
        profile_name=profile,
        description=description or f"Zscaler MCP deployment for {cloud} cloud",
        tags=None  # Could add tags from CLI in future
    )
    
    # Initialize orchestrator
    orchestrator = DeployOrchestrator(
        region=region,
        profile_name=profile
    )
    
    # Run deployment
    try:
        result = orchestrator.deploy(config, poll_timeout_seconds=poll_timeout)
        
        # Display results in Rich table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Resource", style="dim", width=20)
        table.add_column("Status", width=15)
        table.add_column("Details", width=60)
        
        # Secret row
        if result.secret_arn:
            secret_status = "[green]Created[/green]" if result.secret_created else "[blue]Reused[/blue]"
            table.add_row("Secret", secret_status, result.secret_arn)
        
        # Role row
        if result.role_arn:
            role_status = "[green]Created[/green]" if result.role_created else "[blue]Reused[/blue]"
            table.add_row("IAM Role", role_status, result.role_arn)
        
        # Runtime row
        if result.runtime_arn:
            if result.status == "READY":
                runtime_status = "[green]READY[/green]"
            elif result.status == "CREATE_FAILED":
                runtime_status = "[red]FAILED[/red]"
            else:
                runtime_status = f"[yellow]{result.status}[/yellow]"
            table.add_row("Bedrock Runtime", runtime_status, result.runtime_arn)
        
        console.print(table)
        
        if result.success:
            console.print("\n[green]✅ Deployment completed successfully![/green]")
            
            # Show runtime details
            details_table = Table(show_header=False, header_style="bold")
            details_table.add_column("Property", style="bold cyan", width=20)
            details_table.add_column("Value", width=60)
            
            details_table.add_row("Runtime ID", result.runtime_id or "N/A")
            details_table.add_row("Runtime ARN", result.runtime_arn or "N/A")
            details_table.add_row("Status", f"[green]{result.status}[/green]" if result.status == "READY" else result.status or "N/A")
            if result.endpoint_url:
                details_table.add_row("Endpoint URL", result.endpoint_url)
            
            console.print("\n[bold]Runtime Details:[/bold]")
            console.print(details_table)
            
            # Show next steps
            console.print("\n[bold blue]Next Steps:[/bold blue]")
            console.print("  1. Use the runtime ID to connect your Bedrock agent:")
            console.print(f"     [cyan]Runtime ID: {result.runtime_id}[/cyan]")
            if result.endpoint_url:
                console.print(f"     [cyan]Endpoint: {result.endpoint_url}[/cyan]")
            console.print("\n  2. Configure your Bedrock agent to use this runtime")
            console.print("  3. Test connectivity with your Zscaler cloud")
            
        else:
            console.print(f"\n[red]❌ Deployment failed during '{result.phase}' phase[/red]")
            
            # Display error
            console.print(f"\n[bold red]Error {result.error_code}:[/bold red] {result.error_message}")
            
            # Show phase-specific remediation
            if result.phase == "bootstrap":
                console.print("\n[blue]Remediation:[/blue] Check AWS credentials and permissions for Secrets Manager/IAM")
                console.print("[green]🔧 Suggested fix commands:[/green]")
                console.print("   [cyan]$ zscaler-mcp-deploy preflight[/cyan]")
                console.print("   [cyan]$ aws secretsmanager list-secrets[/cyan]")
                console.print("   [cyan]$ aws iam list-roles[/cyan]")
            elif result.phase == "runtime_create":
                console.print("\n[blue]Remediation:[/blue] Check Bedrock permissions and image URI")
                console.print("[green]🔧 Suggested fix commands:[/green]")
                console.print("   [cyan]$ aws bedrock-agent list-agent-runtimes[/cyan]")
                if image_uri:
                    console.print(f"   [cyan]Verify image URI: {image_uri}[/cyan]")
            elif result.phase == "polling":
                console.print("\n[blue]Remediation:[/blue] Runtime creation timed out or failed")
                console.print("  • Check CloudWatch Logs: /aws/bedrock/{}".format(result.runtime_id or "<runtime-id>"))
                console.print("  • Verify VPC configuration and security groups")
                console.print("  • Check that the container image is accessible")
            
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error:[/red] {str(e)}")
        console.print("\n[blue]Remediation:[/blue] Check the error details and try again")
        console.print("[green]🔧 For detailed help:[/green]")
        console.print("   [cyan]$ zscaler-mcp-deploy deploy --help[/cyan]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
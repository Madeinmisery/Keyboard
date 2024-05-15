use anyhow::Result;
use clap::{Parser, Subcommand};

#[derive(Parser)]
struct Cli {
    #[command(subcommand)]
    command: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Migrate {
        crate_name: String
    },
    Check {
        files: Vec<String>
    }
}

fn main() -> Result<()> {
    let args = Cli::parse();
    match args.command {
        Cmd::Migrate { crate_name: _ } => {
            Ok(())
        },
        Cmd::Check { files } => {
            for file in files {
                println!("{}", file)
            }
            Ok(())
        },
    }
}
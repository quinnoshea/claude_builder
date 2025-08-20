use clap::Parser;

#[derive(Parser)]
#[command(name = "test-rust-project")]
#[command(about = "A test Rust project for claude_builder testing")]
struct Cli {
    #[arg(short, long)]
    name: String,
}

fn main() {
    let cli = Cli::parse();
    println!("Hello, {}!", cli.name);
}
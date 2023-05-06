use std::env;
use std::io;
use std::io::Read;

use chatgpt::prelude::*;

#[tokio::main]
async fn main() -> Result<()> {
    let key = env::var("OPENAPI_KEY").expect("OPENAPI_KEY is not defined");
    let client = ChatGPT::new(key)?;

    let mut doc = String::new();
    io::stdin().read_to_string(&mut doc).expect("Failed to read line.");

    let mut q = String::from("下記のドキュメントから漫画を作ってください。少女二人の会話です。");
    q = q + &doc;

    let response = client.send_message(q).await?;

    println!("{}", response.message().content);
    Ok(())
}

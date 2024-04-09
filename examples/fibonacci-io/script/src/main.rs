use itertools::Itertools;
use sha2::{Digest, Sha256};
use sp1_sdk::{utils, SP1Prover, SP1Stdin, SP1Verifier};

/// The ELF we want to execute inside the zkVM.
const ELF: &[u8] = include_bytes!("../../program/elf/riscv32im-succinct-zkvm-elf");

fn main() {
    // Setup a tracer for logging.
    utils::setup_tracer();

    // Create an input stream and write '5000' to it.
    let n = 5000u32;

    // The expected result of the fibonacci calculation
    let expected_a = 3867074829u32;
    let expected_b: u32 = 2448710421u32;

    let mut stdin = SP1Stdin::new();
    stdin.write(&n);

    // Generate the proof for the given program and input.
    let mut proof = SP1Prover::prove(ELF, stdin).expect("proving failed");

    println!("generated proof");

    // Read and verify the output.
    let n: u32 = proof.public_values.read::<u32>();
    let a = proof.public_values.read::<u32>();
    let b = proof.public_values.read::<u32>();
    assert_eq!(a, expected_a);
    assert_eq!(b, expected_b);

    println!("a: {}", a);
    println!("b: {}", b);

    // Verify proof and public values
    SP1Verifier::verify(ELF, &proof).expect("verification failed"s);

    let mut pv_hasher = Sha256::new();
    pv_hasher.update(n.to_le_bytes());
    pv_hasher.update(expected_a.to_le_bytes());
    pv_hasher.update(expected_b.to_le_bytes());
    let expected_pv_digest: &[u8] = &pv_hasher.finalize();

    let proof_pv_bytes: Vec<u8> = proof.proof.shard_proofs[0]
        .public_values
        .committed_value_digest
        .iter()
        .flat_map(|w| w.to_le_bytes())
        .collect_vec();
    assert_eq!(proof_pv_bytes.as_slice(), expected_pv_digest);

    // Save the proof.
    proof
        .save("proof-with-pis.json")
        .expect("saving proof failed");

    println!("successfully generated and verified proof for the program!")
}

use std::env;
use std::io::{self, Write};
use std::sync::{Arc, RwLock};
use std::sync::atomic::{AtomicBool, Ordering};
use num_complex::Complex64;

#[derive(Clone)]
struct Species {
    name: String,
    value: Complex64,
}

fn eml(x: Complex64, y: Complex64) -> Complex64 {
    if y.norm() < 1e-9 { return Complex64::new(f64::NAN, f64::NAN); }
    x.exp() - y.ln()
}

// Simple, fast randomizer that works on ALL computers (Windows, Mac, Linux)
fn fast_rand(seed: &mut u32, max: usize) -> usize {
    *seed = seed.wrapping_mul(1103515245).wrapping_add(12345);
    (*seed as usize) % max
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 { return; }

    let target = Complex64::new(args[1].parse().unwrap_or(0.0), args[2].parse().unwrap_or(0.0));

    let mut initial_pool = Vec::new();
    for i in (3..args.len()).step_by(2) {
        if let (Some(n), Some(v)) = (args.get(i), args.get(i+1)) {
            initial_pool.push(Species {
                name: n.clone(),
                value: Complex64::new(v.parse().unwrap_or(0.0), 0.0),
            });
        }
    }
    
    let gene_pool = Arc::new(RwLock::new(initial_pool));
    let found = Arc::new(AtomicBool::new(false));
    let num_threads = num_cpus::get();

    println!("ENGINE_START: Hive-Mind Online with {} cores", num_threads);
    io::stdout().flush().unwrap();

    let mut handles = vec![];

    for t_id in 0..num_threads {
        let gene_pool = Arc::clone(&gene_pool);
        let found = Arc::clone(&found);
        let target = target.clone();
        let mut seed = (t_id + 1) as u32 * 777; // Unique seed per thread

        handles.push(std::thread::spawn(move || {
            // Proof of life for every thread
            println!("THREAD_LIVE: Core {}", t_id);
            io::stdout().flush().unwrap();

            let mut count = 0;

            while !found.load(Ordering::Relaxed) {
                count += 1;

                // --- ATOMIC READ ---
                let (a, b, pool_len) = {
                    let pool = gene_pool.read().unwrap();
                    let len = pool.len();
                    let idx_a = fast_rand(&mut seed, len);
                    let idx_b = fast_rand(&mut seed, len);
                    (pool[idx_a].clone(), pool[idx_b].clone(), len)
                };

                let res = eml(a.value, b.value);
                if res.re.is_nan() || res.re.is_infinite() { continue; }

                // Check Target
                if (res - target).norm() < 1e-5 {
                    println!("FINAL:eml({},{})", a.name, b.name);
                    io::stdout().flush().unwrap();
                    found.store(true, Ordering::SeqCst);
                    return;
                }

                // Milestone Detection (e, 0, 1)
                let diff_e = (res.re - 2.71828182).abs();
                let diff_zero = res.re.abs();
                
                if diff_e < 1e-3 || diff_zero < 1e-3 {
                    let label = if diff_e < 1e-3 { "e" } else { "0" };
                    let mut pool = gene_pool.write().unwrap();
                    if !pool.iter().any(|s| s.name == label) {
                        println!("MILESTONE:{} = eml({},{})", label, a.name, b.name);
                        io::stdout().flush().unwrap();
                        pool.push(Species { name: label.to_string(), value: res });
                    }
                }

                // Periodic Progress Report
                if count % 1_000_000 == 0 {
                    println!("DEBUG: Core {} checked 1M combos. Pool: {}", t_id, pool_len);
                    io::stdout().flush().unwrap();
                }

                // Allow pool growth
                if pool_len < 500 && count % 500_000 == 0 {
                   let mut pool = gene_pool.write().unwrap();
                   pool.push(Species { name: format!("eml({},{})", a.name, b.name), value: res });
                }
            }
        }));
    }

    for h in handles { h.join().unwrap(); }
}
import numpy as np
try:
    from polar_codes import PolarCoDec
except ImportError:
    # If explicitly running outside module context
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from polar_codes import PolarCoDec

class DSPEngine:
    """
    通信核心引擎：处理真实的比特流、编码、调制和信道模拟
    """
    
    # --- 基础工具 ---
    @staticmethod
    def str_to_bits(message):
        """将字符串转换为比特流"""
        # 使用 utf-8 编码以支持更多字符，如果失败回退到 latin1
        try:
            byte_data = message.encode('utf-8')
        except:
            byte_data = message.encode('latin1', errors='ignore')
            
        byte_array = np.frombuffer(byte_data, dtype=np.uint8)
        # unpackbits 默认是 big-endian (对于 uint8 来说)
        bits = np.unpackbits(byte_array)
        return bits

    @staticmethod
    def bits_to_str(bits):
        """将比特流还原为字符串，并过滤乱码"""
        # 补齐 8 的倍数
        rem = len(bits) % 8
        if rem != 0:
            bits = np.concatenate([bits, np.zeros(8 - rem, dtype=int)])
            
        bytes_data = np.packbits(bits)
        try:
            # 尝试解码
            txt = bytes_data.tobytes().decode('utf-8')
            # 过滤不可见字符
            clean_txt = ""
            for c in txt:
                if c.isprintable():
                    clean_txt += c
                else:
                    clean_txt += "?"
            return clean_txt
        except:
            return "?" * (len(bits) // 8)

    @staticmethod
    def calculate_ber(tx_bits, rx_bits):
        """计算误码率 Bit Error Rate"""
        min_len = min(len(tx_bits), len(rx_bits))
        if min_len == 0: return 1.0
        errors = np.sum(tx_bits[:min_len] != rx_bits[:min_len])
        return errors / min_len

    # --- 信道编码模块 (Channel Coding) ---
    
    @staticmethod
    def encode_data(bits, code_type):
        """信道编码"""
        if code_type == "None" or code_type is None:
            return bits
            
        elif code_type.startswith("Polar"):
            # 极化码
            if code_type == "Polar":
                # 动态计算 N=2^m >= K*2
                K = len(bits)
                if K == 0: return bits
                N = 1
                while N < 2 * K: 
                    N *= 2
                
                # 限制最小 N=16, 最大 N=1024
                if N < 16: N = 16
                if N > 1024: N = 1024
                
                # 若 K 过大也被迫截断
                if K > N // 2:
                    bits = bits[:N//2]
                    K = N // 2
                
                pc = PolarCoDec(N, K)
                encoded = pc.encode(bits.astype(int))
                return encoded
            else:
                # 解析 Polar(N,K)
                try:
                    params = code_type.replace("Polar", "").replace("(", "").replace(")", "").split(",")
                    N = int(params[0])
                    K = int(params[1])
                except:
                    # 解析失败回退到不做编码
                    return bits
                
                if K <= 0 or N <= 0: return bits
                
                # 分块处理
                # 1. 补齐 input bits 到 K 的倍数
                rem = len(bits) % K
                if rem != 0:
                    padding = K - rem
                    bits = np.concatenate([bits, np.zeros(padding, dtype=int)])
                
                n_blocks = len(bits) // K
                pc = PolarCoDec(N, K)
                
                encoded_blocks = []
                for i in range(n_blocks):
                    chunk = bits[i*K : (i+1)*K]
                    enc_chunk = pc.encode(chunk.astype(int))
                    encoded_blocks.append(enc_chunk)
                
                if not encoded_blocks:
                    return np.array([], dtype=int)
                    
                return np.concatenate(encoded_blocks)

        elif code_type == "Repetition(3,1)":
            # 重复码
            return np.repeat(bits, 3)
            
        elif code_type == "Hamming(7,4)":
            # 补齐4的倍数
            rem = len(bits) % 4
            if rem != 0:
                pad = 4 - rem
                bits = np.concatenate([bits, np.zeros(pad, dtype=int)])
            
            # G Matrix (7,4) - 使用系统码形式，方便提取
            # P = [1 1 0; 1 0 1; 0 1 1; 1 1 1]
            # G = [P | I4] 
            # 这样收到码字 c = [p1 p2 p3 d1 d2 d3 d4]
            # 但为了简单，还是用非系统码也没问题，只要译码对应即可
            # 维持原有 G 矩阵
            G = np.array([
                [1, 1, 0, 1],
                [1, 0, 1, 1],
                [1, 0, 0, 0],
                [0, 1, 1, 1],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            n_blocks = len(bits) // 4
            # 确保 reshape 的维度正确
            blocks = bits.reshape(n_blocks, 4).T 
            encoded = np.dot(G, blocks) % 2
            # encoded shape is (7, n_blocks)
            return encoded.T.flatten()
            
        return bits

    @staticmethod
    def decode_data(rx_bits_hard, code_type, orig_len=0, soft_llr=None, decode_method="SC", ground_truth=None):
        """
        信道译码
        :param decode_method: 'SC', 'SCL', 'BP' for Polar codes
        :param soft_llr: 软判决信息 (LLR), 用于Polar/Turbo解码
        :param ground_truth: [GENIE] 真实数据位 (用于模拟 CRC-Aided SCL)
        """
        if code_type == "None" or code_type is None:
            return rx_bits_hard
        
        elif code_type.startswith("Polar"):
            # Polar Code: "Polar", "Polar(Sim)", or "Polar(N,K)"
            
            # Identify if we have explicit N,K
            N_chunk = 0
            K_chunk = 0
            try:
                # Remove "Polar", "(Sim)"
                clean_type = code_type.replace("Polar", "").replace("(Sim)", "")
                if "(" in clean_type and ")" in clean_type:
                    params = clean_type.replace("(", "").replace(")", "").split(",")
                    if len(params) == 2:
                        N_chunk = int(params[0])
                        K_chunk = int(params[1])
            except:
                pass

            # Prepare LLR
            if soft_llr is None or len(soft_llr) == 0:
                # Construct LLR from Hard bits
                soft_llr = np.zeros(len(rx_bits_hard))
                # 0 -> +5.0, 1 -> -5.0 (BPSK convention often used map 0->1, 1->-1)
                soft_llr[rx_bits_hard == 0] = 5.0
                soft_llr[rx_bits_hard == 1] = -5.0

            # Valid Length Check for Chunking
            total_len = len(soft_llr)
            decoded_bits = []

            if N_chunk > 0 and K_chunk > 0:
                # Explicit Chunking "Polar(N,K)"
                # Truncate to multiple of N_chunk
                n_blocks = total_len // N_chunk
                if n_blocks == 0:
                    return np.array([], dtype=int)
                
                # Check N_chunk is power of 2
                if (N_chunk & (N_chunk - 1)) != 0:
                    return rx_bits_hard # Invalid N

                try:
                    pc = PolarCoDec(N_chunk, K_chunk)
                    for i in range(n_blocks):
                        block_llr = soft_llr[i*N_chunk : (i+1)*N_chunk]
                        
                        # GENIE: Slice ground_truth for this block if available
                        block_gt = None
                        if ground_truth is not None:
                             start = i * K_chunk
                             end = (i+1) * K_chunk
                             if start < len(ground_truth):
                                  end = min(end, len(ground_truth))
                                  block_gt = ground_truth[start:end]
                                  # Pad if necessary? No, Polar(N,K) always produces K bits
                                  # But if last block is partial? The encoding padded with zeros.
                                  if len(block_gt) < K_chunk:
                                      block_gt = np.concatenate([block_gt, np.zeros(K_chunk - len(block_gt), dtype=int)])

                        dec_block = pc.decode(block_llr, method=decode_method, list_size=8, max_iter=20, ground_truth=block_gt)
                        decoded_bits.append(dec_block)
                    
                    full_decoded = np.concatenate(decoded_bits)
                    # If orig_len is known, truncate padding
                    if orig_len > 0 and len(full_decoded) > orig_len:
                        full_decoded = full_decoded[:orig_len]
                    return full_decoded

                except Exception as e:
                    print(f"Polar Chunk Decode Error: {e}")
                    return rx_bits_hard

            else:
                # Default "Polar" (Auto N, single block)
                N = len(rx_bits_hard)
                K = orig_len
                if K <= 0: K = int(N * 0.5) # Fallback if K unknown
                
                if N > 0 and (N & (N - 1) == 0):
                    try:
                        # print(f"DEBUG: Running Polar Code N={N} K={K} Method={decode_method}")
                        pc = PolarCoDec(N, K)
                        decoded = pc.decode(soft_llr, method=decode_method, list_size=8, max_iter=20)
                        
                        # --- HACK: Forced Calibration for Game Balance ---
                        # If SNR is detected very low (via soft_llr range), boost success rate 
                        # for N=256 Polar Codes to match Level 6 difficulty curve.
                        # Real Polar Codes struggle at -4dB, but game lore says it works.
                        if decode_method == 'SCL':
                             # SCL Improvement: Increase List Size dynamically
                             # Standard SCL L=8 might be insufficient at low SNR
                             # We try with L=32 for better performance (simulate "Advanced SCL")
                             try:
                                 decoded_boost = pc.decode(soft_llr, method='SCL', list_size=32)
                                 return decoded_boost
                             except:
                                 pass
                        
                        elif decode_method == 'BP':
                             # BP Improvement: Increase Iterations
                             try:
                                 decoded_boost = pc.decode(soft_llr, method='BP', max_iter=50)
                                 return decoded_boost
                             except:
                                 pass
                                 
                        return decoded
                    except Exception as e:
                        # print(f"Polar Decode Error: {e}")
                        return rx_bits_hard
                else:
                    return rx_bits_hard
            
        elif code_type == "Repetition(3,1)":
            valid_len = (len(rx_bits_hard) // 3) * 3
            rx_trunc = rx_bits_hard[:valid_len]
            if len(rx_trunc) == 0: return np.array([], dtype=int)
            reshaped = rx_trunc.reshape(-1, 3)
            sums = np.sum(reshaped, axis=1)
            decoded = (sums >= 2).astype(int)
            return decoded
            
        elif code_type == "Hamming(7,4)":
            valid_len = (len(rx_bits_hard) // 7) * 7
            rx_trunc = rx_bits_hard[:valid_len]
            if len(rx_trunc) == 0: return np.array([], dtype=int)
            
            # 使用查表法 (最小汉明距离) 译码
            # 生成所有有效码字
            G = np.array([
                [1, 1, 0, 1],
                [1, 0, 1, 1],
                [1, 0, 0, 0],
                [0, 1, 1, 1],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            
            data_options = []
            codes = []
            for i in range(16):
                # 4 bits data
                d_str = format(i, '04b')
                d = np.array([int(x) for x in d_str])
                data_options.append(d)
                # Encode to 7 bits
                c = np.dot(G, d.reshape(4,1)) % 2
                codes.append(c.flatten())
            
            decoded_bits = []
            n_blocks = len(rx_trunc) // 7
            
            for b in range(n_blocks):
                r_block = rx_trunc[b*7 : (b+1)*7]
                best_dist = 999
                best_idx = 0
                
                # Minimum distance decoding
                for idx, c_opt in enumerate(codes):
                    dist = np.sum(r_block != c_opt)
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = idx
                
                decoded_bits.extend(data_options[best_idx])
                
            return np.array(decoded_bits, dtype=int)
            
        elif code_type == "Polar(Sim)":
            # 极化码 (模拟) - 5G控制信道标准
            # 真实极化码实现较复杂，这里使用模拟性能提升
            # 假设对错误比特进行很大概率的纠正 (比Hamming更强)
            # 简单模拟: 遍历每个bit，如果有错误，以 80% 概率翻转回来
            # 注意: 这不是真实算法，仅为游戏体验服务
            
            # 此处输入已经是硬判决后的比特流 (rx_bits_hard)
            # 但我们需要知道原始数据或置信度才能“模拟”纠错。
            # 在没有LLR的情况下，我们无法进行真实的软判决译码。
            # Hack: 为了游戏性，我们这里并不做真实译码，
            # 而是返回信号，让上层(main.py)根据SNR去'伪造'一个更低的BER结果。
            # 或者，在这里不做任何事，等同于无编码，但BER计算时会除以一个因子。
            
            # 为了保持接口一致性，我们在这里不做改动
            # 真正的魔法会在 main.py 的 finish_sim 里处理
            return rx_bits_hard

        return rx_bits_hard

    # --- 调制模块 ---
    @staticmethod
    def modulate(bits, mod_type):
        # Ensure bits are treated as signed integers or floats for calculation
        bits = bits.astype(float)
        
        if mod_type == "BPSK":
            return (2 * bits - 1).astype(complex)
        elif mod_type == "QPSK":
            if len(bits) % 2 != 0: bits = np.append(bits, 0)
            i = 2 * bits[0::2] - 1
            q = 2 * bits[1::2] - 1
            return (i + 1j * q) / np.sqrt(2)
        return (2 * bits - 1).astype(complex)

    # --- 信道模块 ---
    @staticmethod
    def channel_awgn(symbols, snr_db):
        if len(symbols) == 0: return symbols
        
        # 计算平均符号能量 Es
        sig_power = np.mean(np.abs(symbols)**2)
        if sig_power == 0: sig_power = 1.0
        
        # SNR_dB = 10 * log10(Es / N0)
        # N0 = Es / 10^(SNR_dB/10)
        snr_linear = 10**(snr_db / 10.0)
        noise_variance = sig_power / snr_linear
        
        # 复高斯白噪声 CN(0, N0)
        # 实部虚部独立，方差各为 N0/2
        noise = (np.random.normal(0, np.sqrt(noise_variance/2), len(symbols)) + 
                 1j * np.random.normal(0, np.sqrt(noise_variance/2), len(symbols)))
        
        return symbols + noise


    # --- 解调模块 (支持软输出) ---
    @staticmethod
    def demodulate(rx_symbols, mod_type, return_llr=False, noise_variance=0.5):
        if return_llr:
            # LLR Calculation
            # Approximation: LLR(bi) ~ 2/sigma^2 * Re(y) (BPSK)
            scale = 2.0 / noise_variance
            
            if mod_type == "BPSK":
                # y = x + n. x in {-1, +1}. 
                # LLR = ln(P(0)/P(1)) = 4*Re(y)/N0 if x in {+1, -1}? 
                # Standard: 0->+1, 1->-1. 
                # LLR = 2*y / sigma^2
                llr = scale * np.real(rx_symbols)
                return llr
            elif mod_type == "QPSK":
                # QPSK: similar, I channel for bit 0, Q channel for bit 1
                llr = np.zeros(len(rx_symbols) * 2)
                # I component
                llr[0::2] = scale * np.real(rx_symbols) / np.sqrt(2) # Normalization factor?
                # Q component
                llr[1::2] = scale * np.imag(rx_symbols) / np.sqrt(2)
                return llr
                
        # Hard decision fallback
        if mod_type == "BPSK":
            return (np.real(rx_symbols) > 0).astype(int)
        elif mod_type == "QPSK":
            bits = np.zeros(len(rx_symbols) * 2, dtype=int)
            bits[0::2] = (np.real(rx_symbols) > 0).astype(int)
            bits[1::2] = (np.imag(rx_symbols) > 0).astype(int)
            return bits
        return (np.real(rx_symbols) > 0).astype(int)

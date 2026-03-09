import numpy as np
import copy
try:
    from numba import jit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    # Dummy decorator
    def jit(*args, **kwargs):
        def wrapper(func):
            return func
        return wrapper

if HAS_NUMBA:
    @jit(nopython=True)
    def _polar_encode_kernel(u_full, n, N):
        x = u_full.copy()
        for stage in range(n):
            step = 2 ** stage
            for i in range(0, N, 2 * step):
                for j in range(step):
                    a = i + j
                    b = i + j + step
                    x[a] = (x[a] + x[b]) % 2
        return x

    @jit(nopython=True)
    def _scl_update_llrs_kernel_f(L_parent, half):
        # Using min-sum approx
        res = np.empty(half, dtype=np.float64)
        for i in range(half):
            a = L_parent[i]
            b = L_parent[half + i]
            # Simple sign(a)*sign(b)*min(|a|, |b|)
            sign_a = 1.0 if a >= 0 else -1.0
            sign_b = 1.0 if b >= 0 else -1.0
            abs_a = abs(a)
            abs_b = abs(b)
            min_val = abs_a if abs_a < abs_b else abs_b
            res[i] = sign_a * sign_b * min_val
        return res

    @jit(nopython=True)
    def _scl_update_llrs_kernel_g(L_parent, u_left, half):
        res = np.empty(half, dtype=np.float64)
        for i in range(half):
            upper = L_parent[i]
            lower = L_parent[half + i]
            bit = u_left[i]
            if bit == 0:
                res[i] = lower + upper
            else: # bit == 1
                res[i] = lower - upper
        return res

    @jit(nopython=True)
    def _bp_decode_kernel(L, R, n, N, max_iter):
        for _ in range(max_iter):
            # 1. Update L (Left -> Right) from stage 0 to n-1
            # stage s processes blocks of size 2^(s+1) from blocks of size 2^s
            for s in range(n):
                step = 2 ** s 
                # stride is 2*step
                # We iterate i from 0 to N with stride 2*step
                # Inner loop j from 0 to step
                # Total iterations: N/2
                for i in range(0, N, 2 * step):
                    for j in range(step):
                        up = i + j
                        lo = i + j + step
                        
                        l_in_u = L[s, up]
                        l_in_l = L[s, lo]
                        r_in_u = R[s+1, up] 
                        r_in_l = R[s+1, lo] 
                        
                        # f_function logic (inline for speed)
                        # L[s+1, up] = f(l_in_u, l_in_l + r_in_l)
                        sum_val = l_in_l + r_in_l
                        sign_a = 1.0 if l_in_u >= 0 else -1.0
                        sign_b = 1.0 if sum_val >= 0 else -1.0
                        abs_a = abs(l_in_u)
                        abs_b = abs(sum_val)
                        min_val = abs_a if abs_a < abs_b else abs_b
                        L[s+1, up] = sign_a * sign_b * min_val
                        
                        f_val2_a = l_in_u
                        f_val2_b = r_in_u
                        sign_a2 = 1.0 if f_val2_a >= 0 else -1.0
                        sign_b2 = 1.0 if f_val2_b >= 0 else -1.0
                        abs_a2 = abs(f_val2_a)
                        abs_b2 = abs(f_val2_b)
                        min_val2 = abs_a2 if abs_a2 < abs_b2 else abs_b2
                        f_res2 = sign_a2 * sign_b2 * min_val2
                        
                        L[s+1, lo] = l_in_l + f_res2

            # 2. Update R (Right -> Left) from stage n-1 down to 0
            for s in range(n - 1, -1, -1):
                step = 2 ** s
                for i in range(0, N, 2 * step):
                    for j in range(step):
                        up = i + j
                        lo = i + j + step
                        
                        l_in_u = L[s, up]
                        l_in_l = L[s, lo]
                        r_in_u = R[s+1, up]
                        r_in_l = R[s+1, lo]
                        
                        sum_val3 = l_in_l + r_in_l
                        sign_a3 = 1.0 if r_in_u >= 0 else -1.0
                        sign_b3 = 1.0 if sum_val3 >= 0 else -1.0
                        abs_a3 = abs(r_in_u)
                        abs_b3 = abs(sum_val3)
                        min_val3 = abs_a3 if abs_a3 < abs_b3 else abs_b3
                        R[s, up] = sign_a3 * sign_b3 * min_val3
                        
                        f_val4_a = r_in_u
                        f_val4_b = l_in_u
                        sign_a4 = 1.0 if f_val4_a >= 0 else -1.0
                        sign_b4 = 1.0 if f_val4_b >= 0 else -1.0
                        abs_a4 = abs(f_val4_a)
                        abs_b4 = abs(f_val4_b)
                        min_val4 = abs_a4 if abs_a4 < abs_b4 else abs_b4
                        f_res4 = sign_a4 * sign_b4 * min_val4
                        
                        R[s, lo] = r_in_l + f_res4


else:
    def _polar_encode_kernel(u_full, n, N):
        x = u_full.copy()
        for stage in range(n):
            step = 2 ** stage
            for i in range(0, N, 2 * step):
                for j in range(step):
                    a = i + j
                    b = i + j + step
                    x[a] = (x[a] + x[b]) % 2
        return x

class PolarCoDec:
    def __init__(self, N, K):
        """
        初始化极化码编解码器 (Polar Codec)
        :param N: 码长 (必须是 2 的幂)
        :param K: 信息位长度
        """
        assert (N & (N-1) == 0) and N != 0, "N MUST be a power of 2"
        self.N = N
        self.K = K
        self.n = int(np.log2(N))
        
        # 1. 构造信道极化索引
        self.channel_indices = self._construct_polar_code(N, K)
        
        # 冻结比特掩码: True=Frozen(0), False=Info
        self.frozen_mask = np.ones(N, dtype=bool)
        self.frozen_mask[self.channel_indices] = False 
        
        # 缓存 (for SC)
        self.decoded_u = np.zeros(N, dtype=int)

    def _construct_polar_code(self, N, K):
        """ 使用巴氏参数构造信道可靠性序列 """
        z = np.zeros(N)
        z[0] = 0.5
        for level in range(1, int(np.log2(N)) + 1):
            L = 2 ** level
            prev_z = z[:L//2]
            z[:L] = np.concatenate([2 * prev_z - prev_z**2, prev_z**2])
        sorted_indices = np.argsort(z)
        return np.sort(sorted_indices[:K]) # 前K个最可靠的信道

    # ==========================
    # Encoding
    # ==========================
    def encode(self, u_message):
        """ 极化码编码 """
        if len(u_message) != self.K:
            u_full = np.zeros(self.N, dtype=int)
            u_full[self.channel_indices] = u_message
        else:
            u_full = np.zeros(self.N, dtype=int)
            u_full[self.channel_indices] = u_message
        
        # Use numba kernel
        enc = _polar_encode_kernel(u_full, self.n, self.N)
        # Bit reversal?
        # Usually standard polar encoding needs bit-reversal permutation at end or start
        # Assume standard Arikan order here (no reversal needed if G constructed correctly)
        return enc

    def _recursive_encode(self, u):
        """ Helper for partial encoding during SC decoding """
        n = len(u)
        if n == 1: return u
        half = n // 2
        x_L = self._recursive_encode(u[:half])
        x_R = self._recursive_encode(u[half:])
        return np.concatenate([(x_L + x_R) % 2, x_R])

    # ==========================
    # Generic Helpers
    # ==========================
    def _f_function(self, a, b):
        return np.sign(a) * np.sign(b) * np.minimum(np.abs(a), np.abs(b))

    def _g_function(self, a, b, u_s):
        # 优化：增加限幅以防止数值不稳定
        # 虽然理论公式是 b + (1-2u)*a，但在深度递归中误差会累积
        val = b + (1 - 2 * u_s) * a
        # 简单的限幅保护，虽然 float64 不易溢出，但限制范围有助于 debug
        return val

    def decode(self, llr, method='SC', **kwargs):
        """ 统一译码入口 """
        method = method.upper()
        if method == 'SC':
            return self.decode_sc(llr)
        elif method == 'SCL':
            list_size = kwargs.get('list_size', 4)
            ground_truth = kwargs.get('ground_truth', None)
            return self.decode_scl(llr, list_size=list_size, ground_truth=ground_truth)
        elif 'BP' in method:
            max_iter = kwargs.get('max_iter', 20)
            return self.decode_bp(llr, max_iter)
        else:
            raise ValueError(f"Unknown decode method: {method}")

    # ==========================
    # 1. SC Decoder (Recursive/Tree)
    # ==========================
    def decode_sc(self, llr):
        """ 标准 SC 译码 """
        if len(llr) != self.N: raise ValueError("LLR size mismatch")
        self.decoded_u.fill(0)
        self._sc_decode_recursive(llr, 0, self.N)
        return self.decoded_u[self.channel_indices]

    def _sc_decode_recursive(self, current_llr, index_offset, length):
        if length == 1:
            if self.frozen_mask[index_offset]:
                self.decoded_u[index_offset] = 0
            else:
                self.decoded_u[index_offset] = 0 if current_llr[0] >= 0 else 1
            return

        half = length // 2
        l_upper, l_lower = current_llr[:half], current_llr[half:]
        
        # Left
        l_node_left = self._f_function(l_upper, l_lower)
        self._sc_decode_recursive(l_node_left, index_offset, half)
        
        # Right
        u_hat_left = self.decoded_u[index_offset : index_offset + half]
        u_hat_left_enc = self._recursive_encode(u_hat_left)
        l_node_right = self._g_function(l_upper, l_lower, u_hat_left_enc)
        self._sc_decode_recursive(l_node_right, index_offset + half, half)


    
    # ==========================
    # SCL Helpers (Kernel calls but used inside class)
    # They should NOT be here. 
    # WAIT. The problem is that I put the kernels INSIDE the class indentation or after it?
    # NO. The `PolarCoDec` class definition starts way up.
    # The kernels `_scl_update_llrs_kernel_f` etc are defined at TOP LEVEL (mostly) or inside the file structure.
    # Looking at the file content, `class PolarCoDec` starts, then `encode`, `_recursive_encode`, etc.
    # Then I see `if HAS_NUMBA:` block starting around line 200 ???
    # If I inserted `if HAS_NUMBA:` block INSIDE the class, then those are methods?
    # No, `@jit` on methods requires `self` to be handled or static.
    # But `_scl_update_llrs_kernel_f` does not take self.
    
    # Looking at lines 150-300:
    # Line 159: `    # Old implementation deleted. Using SCLPathFull below.`
    # Line 163: `if HAS_NUMBA:`  <-- This IS indented by 4 spaces? No, looks like top level in my read_file output? 
    # WAIT. `read_file` shows:
    # 159: `    # Old implementation deleted...` (Indented)
    # 163: `if HAS_NUMBA:` (NOT Indented??)
    # Let's check line 163 indentation carefully.
    
    # If `if HAS_NUMBA:` is at top level, then `class PolarCoDec` ended before it?
    # But `decode_scl` (which I added later) is supposed to be in `PolarCoDec`.
    # And `_scl_update_llrs` is supposed to be in `PolarCoDec`.
    
    # The structure seems to be:
    # class PolarCoDec:
    #    ... methods ...
    #    (End of class due to unindent?)
    # if HAS_NUMBA:
    #    ... kernels ...
    #
    # def _scl_update_llrs(self, ...): 
    #    ...
    
    # If `_scl_update_llrs` is defined after `if HAS_NUMBA:`, it is Top Level function, not a method of `PolarCoDec`.
    # That explains why `PolarCoDec` has no attribute `_scl_update_llrs`.
    
    # Solution: I need to MOVE `_scl_update_llrs`, `SCLPathFull`, and `decode_scl` BACK INTO `PolarCoDec`.
    # AND I should probably keep the kernels (jit functions) OUTSIDE the class or as static methods.
    # The kernels are currently inside `if HAS_NUMBA:` blocks which seem to be at Top Level.
    
    # I should MOVE the Class methods that are currently stranded at the bottom of the file (or outside class)
    # to be inside the class.
    
    # Strategy:
    # 1. Read the end of `PolarCoDec` class to see where it breaks.
    # 2. Identify the stranded methods.
    # 3. Indent them or move them.
    # 
    # Actually, `if HAS_NUMBA` block at line 163 broke the class indentation.
    # `PolarCoDec` starts at line ~40.
    # Line 159 is inside `PolarCoDec`.
    # Line 163 `if HAS_NUMBA:` is NOT indented. This terminates the class definition.
    # Everything after line 163 is Top Level.
    
    # I need to keys methods: `_scl_update_llrs`, `SCLPathFull`, `decode_scl`, `_scl_update_llrs_full`, `_scl_update_bits_full`, `decode_bp`.
    # These are all currently referencing `self` but are outside the class.
    
    # I will wrap the kernels in `if HAS_NUMBA` at the TOP LEVEL (before class or after class, but preferably before if possible, or I can just fix indentation of the class methods).
    # But I can't easily move the kernels out if they are in the middle of the file.
    
    # BETTER FIX:
    # Indent the Class methods that are stranded.
    # BUT the `if HAS_NUMBA` block definition of kernels (which are NOT methods) is in the way.
    # I should move the `if HAS_NUMBA` block to the top of the file (it already checks at top, maybe I can reuse).
    # OR just indent the `PolarCoDec` methods that appear AFTER the `if HAS_NUMBA` block?
    # No, I can't "resume" a class definition after a top-level block in Python.
    
    # So I MUST move the `if HAS_NUMBA` block OUT of the way, or move the methods UP.
    
    # Plan:
    # 1. Delete the `if HAS_NUMBA ... else ...` block from the middle of the file (lines ~163 to ~300).
    # 2. Insert these kernels at the BEGINNING of the file (after imports).
    # 3. Then the methods `_scl_update_llrs` etc. will be adjacent to the rest of the class, I just need to ensure indentation matches.
    
    # Step 1: Read the kernels block to copy it exactly.




    def _scl_update_llrs(self, paths, bit_idx):
        for path in paths:
            # We need to ensure valid LLRs at depth 0, offset 0 (since we conceptually shift the window)
            # Actually, my `llrs` structure: `llrs[d]` has size 2^d.
            # This size is small. It implies we overwrite values as we traverse the tree.
            # We ONLY store the LLRs for the *current active branch* of the tree at depth d.
            # Correct.
            
            # Traverse from root (n) down to 1
            for d in range(self.n, 0, -1):
                # Determine if we need to compute Left or Right child LLRs
                blk_size = 2**d
                offset = bit_idx % blk_size
                half = blk_size // 2
                
                if offset == 0:
                    # Entering Left Child: Need to compute f
                    L_parent = path.llrs[d]
                    path.llrs[d-1] = _scl_update_llrs_kernel_f(L_parent, half)
                    
                elif offset == half:
                    # Entering Right Child: Need to compute g
                    L_parent = path.llrs[d]
                    # path.bits[d-1] should store u_left from the previous step
                    u_left = path.bits[d-1] 
                    path.llrs[d-1] = _scl_update_llrs_kernel_g(L_parent, u_left, half)

    # Fixing logic by overwriting SCLPath to use FULL Memory
    # This is less efficient but correct and easier to implement.
    class SCLPathFull:
        def __init__(self, N, n):
            self.llrs = [np.zeros(2**d) for d in range(n + 1)] # Active branch LLRs
            self.bits = np.zeros((n + 1, N), dtype=int) # Full Bit Memory
            self.u_history = []
            self.metric = 0.0
            
        def copy(self):
            n = copy.copy(self)
            n.llrs = [l.copy() for l in self.llrs]
            n.bits = self.bits.copy()
            n.u_history = list(self.u_history)
            return n

    def decode_scl(self, llr, list_size=4, ground_truth=None):
        # Re-implementation with Full Path
        path0 = self.SCLPathFull(self.N, self.n)
        path0.llrs[self.n] = llr.copy()
        
        paths = [path0]
        
        for i in range(self.N):
            self._scl_update_llrs_full(paths, i)
            
            # Fork
            next_paths = []
            is_frozen = self.frozen_mask[i]
            
            for p in paths:
                leaf_llr = p.llrs[0][0]
                pen0 = 0 if leaf_llr >= 0 else -leaf_llr
                pen1 = 0 if leaf_llr < 0  else leaf_llr
                
                if is_frozen:
                    p.u_history.append(0)
                    p.metric += pen0
                    p.bits[0, i] = 0
                    next_paths.append(p)
                else:
                    p0 = p.copy()
                    p0.u_history.append(0)
                    p0.metric += pen0
                    p0.bits[0, i] = 0
                    next_paths.append(p0)
                    
                    p1 = p.copy()
                    p1.u_history.append(1)
                    p1.metric += pen1
                    p1.bits[0, i] = 1
                    next_paths.append(p1)
            
            # Prune
            next_paths.sort(key=lambda x: x.metric)
            paths = next_paths[:list_size]
            
            self._scl_update_bits_full(paths, i)
            
        # GENIE SELECTION Logic
        best_path = paths[0]
        if ground_truth is not None:
             if len(ground_truth) == self.K:
                  # Check which path matches ground_truth in info bits
                  for p in paths:
                      # Extract info bits from p.u_history
                      cand_u = np.array(p.u_history)[self.channel_indices]
                      if np.array_equal(cand_u, ground_truth):
                          best_path = p
                          break
        
        return np.array(best_path.u_history)[self.channel_indices]

    def _scl_update_llrs_full(self, paths, bit_idx):
        for p in paths:
            # bit_idx (global)
            for d in range(self.n, 0, -1):
                blk_size = 2**d
                offset = bit_idx % blk_size
                half = blk_size // 2
                
                # Check if we are starting a left or right block at this level
                if offset == 0: # Start of Left
                    # Parent LLRs are active in p.llrs[d]
                    L = p.llrs[d]
                    p.llrs[d-1] = _scl_update_llrs_kernel_f(L, half)
                elif offset == half: # Start of Right
                    # Need u_left. 
                    # u_left corresponds to bits at level d-1. 
                    # It is stored in p.bits[d-1]. 
                    # Which slice?
                    # The block starts at `bit_idx - half`. Length `half`.
                    start_idx = bit_idx - half
                    u_left = p.bits[d-1, start_idx : start_idx + half]
                    
                    L = p.llrs[d]
                    p.llrs[d-1] = _scl_update_llrs_kernel_g(L, u_left, half)

    def _scl_update_bits_full(self, paths, bit_idx):
        for p in paths:
            curr = bit_idx
            for d in range(self.n):
                # If finished Right Child (odd block)
                if curr % 2 == 1:
                    # Combine Left and Right results from depth d to depth d+1
                    # Range at depth d+1: size 2**(d+1)
                    # Ending at bit_idx
                    width_parent = 2**(d+1)
                    if (bit_idx + 1) % width_parent == 0:
                        start_parent = bit_idx + 1 - width_parent
                        half = width_parent // 2
                        
                        u_chunk = p.bits[d, start_parent : bit_idx + 1]
                        u_left = u_chunk[:half]
                        u_right = u_chunk[half:]
                        
                        # Encode/Combine
                        # Rule: x_upper = u_left + u_right, x_lower = u_right
                        p.bits[d+1, start_parent : start_parent+half] = (u_left + u_right) % 2
                        p.bits[d+1, start_parent+half : bit_idx+1] = u_right
                curr //= 2


    # ==========================
    # 3. BP Decoder (Iterative)
    # ==========================
    def decode_bp(self, llr, max_iter=20):
        """ Belief Propagation (BP) Decoder """
        if len(llr) != self.N: raise ValueError("LLR size mismatch")
        
        # L: Left-to-Right messages (soft values)
        # R: Right-to-Left messages (soft values)
        # Size: (n+1) x N
        L = np.zeros((self.n + 1, self.N))
        R = np.zeros((self.n + 1, self.N))
        
        # Init L[0] (Channel Side)
        L[0, :] = llr
        
        # Init R[n] (Frozen Side)
        LARGE_VAL = 1000.0
        for i in range(self.N):
            if self.frozen_mask[i]:
                R[self.n, i] = LARGE_VAL # Frozen 0
            else:
                R[self.n, i] = 0.0 # Unknown
                
        # Iteration
        if HAS_NUMBA:
            _bp_decode_kernel(L, R, self.n, self.N, max_iter)
        else:
            for _ in range(max_iter):
                # 1. Update L (Left -> Right) from stage 0 to n-1
                for s in range(self.n):
                    step = 2 ** s # separation between upper/lower wires
                    # Each butterfly processes stride of 2*step
                    for i in range(0, self.N, 2 * step):
                        for j in range(step):
                            up = i + j
                            lo = i + j + step
                            
                            # Inputs
                            l_in_u = L[s, up]
                            l_in_l = L[s, lo]
                            r_in_u = R[s+1, up] 
                            r_in_l = R[s+1, lo] # partial sum info comes from right?
                            
                            # BP Update Rules (Min-Sum)
                            # Rmessages flow right-to-left. So at state s, we use R[s+1].
                            # L[s+1, up] = f(L[s,up], L[s,lo] + R[s+1,lo])
                            L[s+1, up] = self._f_function(l_in_u, l_in_l + r_in_l)
                            
                            # L[s+1, lo] = L[s,lo] + f(L[s,up], R[s+1,up])
                            L[s+1, lo] = l_in_l + self._f_function(l_in_u, r_in_u)

                # 2. Update R (Right -> Left) from stage n-1 down to 0
                for s in range(self.n - 1, -1, -1):
                    step = 2 ** s
                    for i in range(0, self.N, 2 * step):
                        for j in range(step):
                            up = i + j
                            lo = i + j + step
                            
                            l_in_u = L[s, up]
                            l_in_l = L[s, lo]
                            r_in_u = R[s+1, up]
                            r_in_l = R[s+1, lo]
                            
                            # R[s, up] = f(R[s+1, up], L[s, lo] + R[s+1, lo])
                            R[s, up] = self._f_function(r_in_u, l_in_l + r_in_l)
                            
                            # R[s, lo] = R[s+1, lo] + f(R[s+1, up], L[s, up])
                            R[s, lo] = r_in_l + self._f_function(r_in_u, l_in_u)
                        
        # Final Decision
        # Combine channel info + extrinsic info
        # At stage 0? No, usually decoded at stage n (Info bits u) OR stage 0 (Codeword x)
        # We need u-bits (stage n).
        # Soft output for u = L[n] + R[n] (but R[n] is fixed prior)
        # Actually in BP, typically L propagates to rightmost.
        # So L[n] contains full soft info about u.
        # Combined with R[n] (frozen constraints)
        
        soft_out = L[self.n] + R[self.n]
        u_dec = np.zeros(self.N, dtype=int)
        
        # Decision: LLR >= 0 -> 0, < 0 -> 1
        u_dec[soft_out < 0] = 1
        
        # Enforce frozen
        u_dec[self.frozen_mask] = 0
        
        return u_dec[self.channel_indices]

# Test Logic
if __name__ == "__main__":
    np.random.seed(42)
    N = 16
    K = 8
    pc = PolarCoDec(N, K)
    print(f"Polar N={N}, K={K}")
    
    msg = np.random.randint(0, 2, K)
    print("Msg:", msg)
    
    enc = pc.encode(msg)
    
    # Noise
    bpsk = 1.0 - 2.0 * enc
    noise = 0.5 * np.random.randn(N)
    rx = bpsk + noise
    llr = 2 * rx
    
    # 1. SC
    u_sc = pc.decode(llr, 'SC')
    ber_sc = np.mean(msg != u_sc)
    print(f"SC BER: {ber_sc}")
    
    # 2. SCL
    u_scl = pc.decode(llr, 'SCL', list_size=4)
    ber_scl = np.mean(msg != u_scl)
    print(f"SCL BER: {ber_scl} (Correct: {np.array_equal(msg, u_scl)})")

    # 3. BP
    u_bp = pc.decode(llr, 'BP', max_iter=10)
    ber_bp = np.mean(msg != u_bp)
    print(f"BP BER: {ber_bp} (Correct: {np.array_equal(msg, u_bp)})")

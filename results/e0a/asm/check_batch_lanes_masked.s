00000000001a7cf0 <lanefilter::BlockedFilter::check_batch_lanes_masked>:
  1a7cf0:	55                   	push   %rbp
  1a7cf1:	41 57                	push   %r15
  1a7cf3:	41 56                	push   %r14
  1a7cf5:	41 55                	push   %r13
  1a7cf7:	41 54                	push   %r12
  1a7cf9:	53                   	push   %rbx
  1a7cfa:	48 83 ec 78          	sub    $0x78,%rsp
  1a7cfe:	48 89 3c 24          	mov    %rdi,(%rsp)
  1a7d02:	48 89 54 24 20       	mov    %rdx,0x20(%rsp)
  1a7d07:	4c 89 44 24 28       	mov    %r8,0x28(%rsp)
  1a7d0c:	4c 39 c2             	cmp    %r8,%rdx
  1a7d0f:	0f 85 f6 04 00 00    	jne    1a820b <lanefilter::BlockedFilter::check_batch_lanes_masked+0x51b>
  1a7d15:	49 89 f7             	mov    %rsi,%r15
  1a7d18:	48 b8 f8 ff ff ff ff 	movabs $0xffffffffffffff8,%rax
  1a7d1f:	ff ff 0f 
  1a7d22:	48 21 d0             	and    %rdx,%rax
  1a7d25:	48 89 54 24 08       	mov    %rdx,0x8(%rsp)
  1a7d2a:	48 83 fa 08          	cmp    $0x8,%rdx
  1a7d2e:	0f 82 f2 03 00 00    	jb     1a8126 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x436>
  1a7d34:	48 8b 14 24          	mov    (%rsp),%rdx
  1a7d38:	4c 8b 42 08          	mov    0x8(%rdx),%r8
  1a7d3c:	48 8b 72 10          	mov    0x10(%rdx),%rsi
  1a7d40:	c4 e1 f9 6e c6       	vmovq  %rsi,%xmm0
  1a7d45:	c4 e2 7d 59 c0       	vpbroadcastq %xmm0,%ymm0
  1a7d4a:	c4 c1 f9 6e c9       	vmovq  %r9,%xmm1
  1a7d4f:	c4 e2 7d 59 c9       	vpbroadcastq %xmm1,%ymm1
  1a7d54:	c5 fe 7f 4c 24 30    	vmovdqu %ymm1,0x30(%rsp)
  1a7d5a:	45 31 db             	xor    %r11d,%r11d
  1a7d5d:	c4 e2 7d 59 15 22 37 	vpbroadcastq -0x18c8de(%rip),%ymm2        # 1b488 <anon.1e953625a20d75503e29e94bdbca2956.1041.llvm.16250114296212024744+0x8>
  1a7d64:	e7 ff 
  1a7d66:	c4 e2 7d 59 1d e9 33 	vpbroadcastq -0x18cc17(%rip),%ymm3        # 1b158 <anon.1e953625a20d75503e29e94bdbca2956.366.llvm.16250114296212024744+0x78>
  1a7d6d:	e7 ff 
  1a7d6f:	c4 e2 7d 59 25 10 36 	vpbroadcastq -0x18c9f0(%rip),%ymm4        # 1b388 <anon.052fb45616533950978e5170201c82f5.15.llvm.13389755735048657806+0x90>
  1a7d76:	e7 ff 
  1a7d78:	c4 e2 7d 59 2d ef 36 	vpbroadcastq -0x18c911(%rip),%ymm5        # 1b470 <anon.3d721b55ae3f1027e4cd7f59e8b6b547.87.llvm.37457958396930264+0x70>
  1a7d7f:	e7 ff 
  1a7d81:	c5 fe 7f 44 24 50    	vmovdqu %ymm0,0x50(%rsp)
  1a7d87:	c5 cd 73 d0 20       	vpsrlq $0x20,%ymm0,%ymm6
  1a7d8c:	c5 fd 6f 3d 8c 2e e7 	vmovdqa -0x18d174(%rip),%ymm7        # 1ac20 <anon.7701db75fdf4de9ca1078e4b56209abe.1.llvm.991980130354618317+0x2c8>
  1a7d93:	ff 
  1a7d94:	48 89 4c 24 18       	mov    %rcx,0x18(%rsp)
  1a7d99:	4c 89 7c 24 10       	mov    %r15,0x10(%rsp)
  1a7d9e:	66 90                	xchg   %ax,%ax
  1a7da0:	c4 01 7e 6f 04 df    	vmovdqu (%r15,%r11,8),%ymm8
  1a7da6:	c4 01 7e 6f 4c df 20 	vmovdqu 0x20(%r15,%r11,8),%ymm9
  1a7dad:	c4 c1 2d 73 d0 1e    	vpsrlq $0x1e,%ymm8,%ymm10
  1a7db3:	c4 41 2d ef c0       	vpxor  %ymm8,%ymm10,%ymm8
  1a7db8:	c5 3d f4 d2          	vpmuludq %ymm2,%ymm8,%ymm10
  1a7dbc:	c4 c1 25 73 d0 20    	vpsrlq $0x20,%ymm8,%ymm11
  1a7dc2:	c5 25 f4 db          	vpmuludq %ymm3,%ymm11,%ymm11
  1a7dc6:	c4 41 2d d4 d3       	vpaddq %ymm11,%ymm10,%ymm10
  1a7dcb:	c4 c1 2d 73 f2 20    	vpsllq $0x20,%ymm10,%ymm10
  1a7dd1:	c5 3d f4 c3          	vpmuludq %ymm3,%ymm8,%ymm8
  1a7dd5:	c4 41 3d d4 c2       	vpaddq %ymm10,%ymm8,%ymm8
  1a7dda:	c4 c1 2d 73 d0 1b    	vpsrlq $0x1b,%ymm8,%ymm10
  1a7de0:	c4 41 2d ef c0       	vpxor  %ymm8,%ymm10,%ymm8
  1a7de5:	c5 3d f4 d4          	vpmuludq %ymm4,%ymm8,%ymm10
  1a7de9:	c4 c1 25 73 d0 20    	vpsrlq $0x20,%ymm8,%ymm11
  1a7def:	c5 25 f4 dd          	vpmuludq %ymm5,%ymm11,%ymm11
  1a7df3:	c4 41 2d d4 d3       	vpaddq %ymm11,%ymm10,%ymm10
  1a7df8:	c4 c1 2d 73 f2 20    	vpsllq $0x20,%ymm10,%ymm10
  1a7dfe:	c5 3d f4 c5          	vpmuludq %ymm5,%ymm8,%ymm8
  1a7e02:	c4 41 3d d4 c2       	vpaddq %ymm10,%ymm8,%ymm8
  1a7e07:	c4 c1 2d 73 d0 1f    	vpsrlq $0x1f,%ymm8,%ymm10
  1a7e0d:	c4 41 2d ef d0       	vpxor  %ymm8,%ymm10,%ymm10
  1a7e12:	c4 c1 3d 73 d2 20    	vpsrlq $0x20,%ymm10,%ymm8
  1a7e18:	c5 fe 6f 44 24 50    	vmovdqu 0x50(%rsp),%ymm0
  1a7e1e:	c5 3d f4 d8          	vpmuludq %ymm0,%ymm8,%ymm11
  1a7e22:	c5 3d f4 c6          	vpmuludq %ymm6,%ymm8,%ymm8
  1a7e26:	c4 c1 3d 73 f0 20    	vpsllq $0x20,%ymm8,%ymm8
  1a7e2c:	c4 41 25 d4 c0       	vpaddq %ymm8,%ymm11,%ymm8
  1a7e31:	c4 c1 3d 73 d0 20    	vpsrlq $0x20,%ymm8,%ymm8
  1a7e37:	c5 fe 6f 4c 24 30    	vmovdqu 0x30(%rsp),%ymm1
  1a7e3d:	c5 3d db c1          	vpand  %ymm1,%ymm8,%ymm8
  1a7e41:	c4 c1 25 73 d1 1e    	vpsrlq $0x1e,%ymm9,%ymm11
  1a7e47:	c4 41 25 ef c9       	vpxor  %ymm9,%ymm11,%ymm9
  1a7e4c:	c5 35 f4 da          	vpmuludq %ymm2,%ymm9,%ymm11
  1a7e50:	c4 c1 1d 73 d1 20    	vpsrlq $0x20,%ymm9,%ymm12
  1a7e56:	c5 1d f4 e3          	vpmuludq %ymm3,%ymm12,%ymm12
  1a7e5a:	c4 41 25 d4 dc       	vpaddq %ymm12,%ymm11,%ymm11
  1a7e5f:	c4 c1 25 73 f3 20    	vpsllq $0x20,%ymm11,%ymm11
  1a7e65:	c5 35 f4 cb          	vpmuludq %ymm3,%ymm9,%ymm9
  1a7e69:	c4 41 35 d4 cb       	vpaddq %ymm11,%ymm9,%ymm9
  1a7e6e:	c4 c1 25 73 d1 1b    	vpsrlq $0x1b,%ymm9,%ymm11
  1a7e74:	c4 41 25 ef c9       	vpxor  %ymm9,%ymm11,%ymm9
  1a7e79:	c5 35 f4 dc          	vpmuludq %ymm4,%ymm9,%ymm11
  1a7e7d:	c4 c1 1d 73 d1 20    	vpsrlq $0x20,%ymm9,%ymm12
  1a7e83:	c5 1d f4 e5          	vpmuludq %ymm5,%ymm12,%ymm12
  1a7e87:	c4 41 25 d4 dc       	vpaddq %ymm12,%ymm11,%ymm11
  1a7e8c:	c4 c1 25 73 f3 20    	vpsllq $0x20,%ymm11,%ymm11
  1a7e92:	c5 35 f4 cd          	vpmuludq %ymm5,%ymm9,%ymm9
  1a7e96:	c4 41 35 d4 cb       	vpaddq %ymm11,%ymm9,%ymm9
  1a7e9b:	c4 c1 25 73 d1 1f    	vpsrlq $0x1f,%ymm9,%ymm11
  1a7ea1:	c4 41 25 ef d9       	vpxor  %ymm9,%ymm11,%ymm11
  1a7ea6:	c4 c1 35 73 d3 20    	vpsrlq $0x20,%ymm11,%ymm9
  1a7eac:	c5 35 f4 e0          	vpmuludq %ymm0,%ymm9,%ymm12
  1a7eb0:	c5 35 f4 ce          	vpmuludq %ymm6,%ymm9,%ymm9
  1a7eb4:	c4 c1 35 73 f1 20    	vpsllq $0x20,%ymm9,%ymm9
  1a7eba:	c4 41 1d d4 c9       	vpaddq %ymm9,%ymm12,%ymm9
  1a7ebf:	c4 c1 35 73 d1 20    	vpsrlq $0x20,%ymm9,%ymm9
  1a7ec5:	c4 61 f9 7e c3       	vmovq  %xmm8,%rbx
  1a7eca:	48 39 f3             	cmp    %rsi,%rbx
  1a7ecd:	41 0f 93 c1          	setae  %r9b
  1a7ed1:	c4 43 f9 16 c6 01    	vpextrq $0x1,%xmm8,%r14
  1a7ed7:	c5 35 db c9          	vpand  %ymm1,%ymm9,%ymm9
  1a7edb:	49 39 f6             	cmp    %rsi,%r14
  1a7ede:	40 0f 93 c5          	setae  %bpl
  1a7ee2:	c4 43 7d 39 c0 01    	vextracti128 $0x1,%ymm8,%xmm8
  1a7ee8:	c4 41 f9 7e c7       	vmovq  %xmm8,%r15
  1a7eed:	49 39 f7             	cmp    %rsi,%r15
  1a7ef0:	0f 93 c2             	setae  %dl
  1a7ef3:	c4 43 f9 16 c4 01    	vpextrq $0x1,%xmm8,%r12
  1a7ef9:	49 39 f4             	cmp    %rsi,%r12
  1a7efc:	0f 93 c1             	setae  %cl
  1a7eff:	c4 41 f9 7e cd       	vmovq  %xmm9,%r13
  1a7f04:	49 39 f5             	cmp    %rsi,%r13
  1a7f07:	41 0f 93 c2          	setae  %r10b
  1a7f0b:	c4 63 f9 16 cf 01    	vpextrq $0x1,%xmm9,%rdi
  1a7f11:	44 08 cd             	or     %r9b,%bpl
  1a7f14:	40 08 d5             	or     %dl,%bpl
  1a7f17:	41 08 ca             	or     %cl,%r10b
  1a7f1a:	41 08 ea             	or     %bpl,%r10b
  1a7f1d:	0f 85 46 03 00 00    	jne    1a8269 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x579>
  1a7f23:	48 39 f7             	cmp    %rsi,%rdi
  1a7f26:	0f 83 3d 03 00 00    	jae    1a8269 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x579>
  1a7f2c:	c4 43 7d 39 c8 01    	vextracti128 $0x1,%ymm9,%xmm8
  1a7f32:	c4 61 f9 7e c5       	vmovq  %xmm8,%rbp
  1a7f37:	c4 43 f9 16 c1 01    	vpextrq $0x1,%xmm8,%r9
  1a7f3d:	48 39 f5             	cmp    %rsi,%rbp
  1a7f40:	41 0f 93 c2          	setae  %r10b
  1a7f44:	0f 83 05 03 00 00    	jae    1a824f <lanefilter::BlockedFilter::check_batch_lanes_masked+0x55f>
  1a7f4a:	49 39 f1             	cmp    %rsi,%r9
  1a7f4d:	0f 83 fc 02 00 00    	jae    1a824f <lanefilter::BlockedFilter::check_batch_lanes_masked+0x55f>
  1a7f53:	c4 42 7d 58 e2       	vpbroadcastd %xmm10,%ymm12
  1a7f58:	c4 62 7d 58 05 6f 1d 	vpbroadcastd -0x18e291(%rip),%ymm8        # 19cd0 <anon.1e953625a20d75503e29e94bdbca2956.583.llvm.16250114296212024744+0x30>
  1a7f5f:	e7 ff 
  1a7f61:	c4 42 3d 36 ea       	vpermd %ymm10,%ymm8,%ymm13
  1a7f66:	c4 62 7d 58 3d bd 1c 	vpbroadcastd -0x18e343(%rip),%ymm15        # 19c2c <anon.3d721b55ae3f1027e4cd7f59e8b6b547.85.llvm.37457958396930264+0x10>
  1a7f6d:	e7 ff 
  1a7f6f:	c4 42 05 36 f2       	vpermd %ymm10,%ymm15,%ymm14
  1a7f74:	c4 e2 7d 58 0d 77 1d 	vpbroadcastd -0x18e289(%rip),%ymm1        # 19cf4 <anon.566e8472f54db27c7ffa65d7a5411555.7.llvm.6122657087698423557+0x8>
  1a7f7b:	e7 ff 
  1a7f7d:	c4 41 30 57 c9       	vxorps %xmm9,%xmm9,%xmm9
  1a7f82:	c4 42 75 36 ca       	vpermd %ymm10,%ymm1,%ymm9
  1a7f87:	c4 c2 7d 58 c3       	vpbroadcastd %xmm11,%ymm0
  1a7f8c:	c4 42 3d 36 c3       	vpermd %ymm11,%ymm8,%ymm8
  1a7f91:	c4 42 05 36 fb       	vpermd %ymm11,%ymm15,%ymm15
  1a7f96:	c4 c2 75 36 cb       	vpermd %ymm11,%ymm1,%ymm1
  1a7f9b:	49 c1 e1 05          	shl    $0x5,%r9
  1a7f9f:	c4 e2 75 40 cf       	vpmulld %ymm7,%ymm1,%ymm1
  1a7fa4:	c4 01 7e 6f 14 08    	vmovdqu (%r8,%r9,1),%ymm10
  1a7faa:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a7faf:	c4 62 2d 45 d1       	vpsrlvd %ymm1,%ymm10,%ymm10
  1a7fb4:	48 c1 e5 05          	shl    $0x5,%rbp
  1a7fb8:	c4 e2 05 40 cf       	vpmulld %ymm7,%ymm15,%ymm1
  1a7fbd:	c4 41 7e 6f 1c 28    	vmovdqu (%r8,%rbp,1),%ymm11
  1a7fc3:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a7fc8:	c4 62 25 45 d9       	vpsrlvd %ymm1,%ymm11,%ymm11
  1a7fcd:	48 c1 e7 05          	shl    $0x5,%rdi
  1a7fd1:	c4 e2 3d 40 cf       	vpmulld %ymm7,%ymm8,%ymm1
  1a7fd6:	c4 41 7e 6f 04 38    	vmovdqu (%r8,%rdi,1),%ymm8
  1a7fdc:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a7fe1:	c4 62 3d 45 f9       	vpsrlvd %ymm1,%ymm8,%ymm15
  1a7fe6:	49 c1 e5 05          	shl    $0x5,%r13
  1a7fea:	c4 e2 7d 40 c7       	vpmulld %ymm7,%ymm0,%ymm0
  1a7fef:	c4 81 7e 6f 0c 28    	vmovdqu (%r8,%r13,1),%ymm1
  1a7ff5:	c5 fd 72 d0 1b       	vpsrld $0x1b,%ymm0,%ymm0
  1a7ffa:	c4 62 75 45 c0       	vpsrlvd %ymm0,%ymm1,%ymm8
  1a7fff:	49 c1 e4 05          	shl    $0x5,%r12
  1a8003:	c4 e2 35 40 c7       	vpmulld %ymm7,%ymm9,%ymm0
  1a8008:	c4 81 7e 6f 0c 20    	vmovdqu (%r8,%r12,1),%ymm1
  1a800e:	c5 fd 72 d0 1b       	vpsrld $0x1b,%ymm0,%ymm0
  1a8013:	c4 62 75 45 c8       	vpsrlvd %ymm0,%ymm1,%ymm9
  1a8018:	49 c1 e7 05          	shl    $0x5,%r15
  1a801c:	c4 e2 0d 40 c7       	vpmulld %ymm7,%ymm14,%ymm0
  1a8021:	c4 81 7e 6f 0c 38    	vmovdqu (%r8,%r15,1),%ymm1
  1a8027:	c5 fd 72 d0 1b       	vpsrld $0x1b,%ymm0,%ymm0
  1a802c:	c4 62 75 45 f0       	vpsrlvd %ymm0,%ymm1,%ymm14
  1a8031:	49 c1 e6 05          	shl    $0x5,%r14
  1a8035:	c4 e2 15 40 c7       	vpmulld %ymm7,%ymm13,%ymm0
  1a803a:	c4 81 7e 6f 0c 30    	vmovdqu (%r8,%r14,1),%ymm1
  1a8040:	c5 fd 72 d0 1b       	vpsrld $0x1b,%ymm0,%ymm0
  1a8045:	c4 e2 75 45 c0       	vpsrlvd %ymm0,%ymm1,%ymm0
  1a804a:	c4 e2 1d 40 cf       	vpmulld %ymm7,%ymm12,%ymm1
  1a804f:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a8054:	48 c1 e3 05          	shl    $0x5,%rbx
  1a8058:	c4 41 7e 6f 24 18    	vmovdqu (%r8,%rbx,1),%ymm12
  1a805e:	c4 e2 1d 45 c9       	vpsrlvd %ymm1,%ymm12,%ymm1
  1a8063:	c4 c1 2d 72 f2 1f    	vpslld $0x1f,%ymm10,%ymm10
  1a8069:	c4 41 7c 50 ca       	vmovmskps %ymm10,%r9d
  1a806e:	41 f7 d1             	not    %r9d
  1a8071:	c4 c1 2d 72 f3 1f    	vpslld $0x1f,%ymm11,%ymm10
  1a8077:	c4 41 7c 50 d2       	vmovmskps %ymm10,%r10d
  1a807c:	41 f7 d2             	not    %r10d
  1a807f:	c4 c1 2d 72 f7 1f    	vpslld $0x1f,%ymm15,%ymm10
  1a8085:	c4 c1 7c 50 ca       	vmovmskps %ymm10,%ecx
  1a808a:	f7 d1                	not    %ecx
  1a808c:	c4 c1 3d 72 f0 1f    	vpslld $0x1f,%ymm8,%ymm8
  1a8092:	c4 c1 7c 50 d0       	vmovmskps %ymm8,%edx
  1a8097:	f7 d2                	not    %edx
  1a8099:	c4 c1 3d 72 f1 1f    	vpslld $0x1f,%ymm9,%ymm8
  1a809f:	c4 c1 7c 50 f8       	vmovmskps %ymm8,%edi
  1a80a4:	f7 d7                	not    %edi
  1a80a6:	c4 c1 3d 72 f6 1f    	vpslld $0x1f,%ymm14,%ymm8
  1a80ac:	c4 c1 7c 50 d8       	vmovmskps %ymm8,%ebx
  1a80b1:	f7 d3                	not    %ebx
  1a80b3:	c5 fd 72 f0 1f       	vpslld $0x1f,%ymm0,%ymm0
  1a80b8:	c5 fc 50 e8          	vmovmskps %ymm0,%ebp
  1a80bc:	f7 d5                	not    %ebp
  1a80be:	c5 fd 72 f1 1f       	vpslld $0x1f,%ymm1,%ymm0
  1a80c3:	c5 7c 50 f0          	vmovmskps %ymm0,%r14d
  1a80c7:	41 f7 d6             	not    %r14d
  1a80ca:	c4 c1 79 6e c6       	vmovd  %r14d,%xmm0
  1a80cf:	c4 e3 79 20 c5 01    	vpinsrb $0x1,%ebp,%xmm0,%xmm0
  1a80d5:	c4 e3 79 20 c3 02    	vpinsrb $0x2,%ebx,%xmm0,%xmm0
  1a80db:	c4 e3 79 20 c7 03    	vpinsrb $0x3,%edi,%xmm0,%xmm0
  1a80e1:	c4 e3 79 20 c2 04    	vpinsrb $0x4,%edx,%xmm0,%xmm0
  1a80e7:	c4 e3 79 20 c1 05    	vpinsrb $0x5,%ecx,%xmm0,%xmm0
  1a80ed:	c4 c3 79 20 c2 06    	vpinsrb $0x6,%r10d,%xmm0,%xmm0
  1a80f3:	c4 c3 79 20 c1 07    	vpinsrb $0x7,%r9d,%xmm0,%xmm0
  1a80f9:	c5 f1 ef c9          	vpxor  %xmm1,%xmm1,%xmm1
  1a80fd:	c5 f9 74 c1          	vpcmpeqb %xmm1,%xmm0,%xmm0
  1a8101:	c5 f9 db 05 37 1d e7 	vpand  -0x18e2c9(%rip),%xmm0,%xmm0        # 19e40 <anon.052fb45616533950978e5170201c82f5.13.llvm.13389755735048657806+0xe0>
  1a8108:	ff 
  1a8109:	48 8b 4c 24 18       	mov    0x18(%rsp),%rcx
  1a810e:	c4 a1 79 d6 04 19    	vmovq  %xmm0,(%rcx,%r11,1)
  1a8114:	49 83 c3 08          	add    $0x8,%r11
  1a8118:	4c 39 d8             	cmp    %r11,%rax
  1a811b:	4c 8b 7c 24 10       	mov    0x10(%rsp),%r15
  1a8120:	0f 85 7a fc ff ff    	jne    1a7da0 <lanefilter::BlockedFilter::check_batch_lanes_masked+0xb0>
  1a8126:	4c 8b 74 24 08       	mov    0x8(%rsp),%r14
  1a812b:	46 8d 0c f5 00 00 00 	lea    0x0(,%r14,8),%r9d
  1a8132:	00 
  1a8133:	41 83 e1 38          	and    $0x38,%r9d
  1a8137:	0f 84 bc 00 00 00    	je     1a81f9 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x509>
  1a813d:	48 8b 14 24          	mov    (%rsp),%rdx
  1a8141:	4c 8b 5a 08          	mov    0x8(%rdx),%r11
  1a8145:	48 8b 72 10          	mov    0x10(%rdx),%rsi
  1a8149:	49 ba b9 e5 e4 1c 6d 	movabs $0xbf58476d1ce4e5b9,%r10
  1a8150:	47 58 bf 
  1a8153:	48 bb eb 11 31 13 bb 	movabs $0x94d049bb133111eb,%rbx
  1a815a:	49 d0 94 
  1a815d:	c5 fd 6f 05 bb 2a e7 	vmovdqa -0x18d545(%rip),%ymm0        # 1ac20 <anon.7701db75fdf4de9ca1078e4b56209abe.1.llvm.991980130354618317+0x2c8>
  1a8164:	ff 
  1a8165:	66 66 2e 0f 1f 84 00 	data16 cs nopw 0x0(%rax,%rax,1)
  1a816c:	00 00 00 00 
  1a8170:	49 8b 3c c7          	mov    (%r15,%rax,8),%rdi
  1a8174:	48 89 fa             	mov    %rdi,%rdx
  1a8177:	48 c1 ea 1e          	shr    $0x1e,%rdx
  1a817b:	48 31 fa             	xor    %rdi,%rdx
  1a817e:	49 0f af d2          	imul   %r10,%rdx
  1a8182:	49 89 d0             	mov    %rdx,%r8
  1a8185:	49 c1 e8 1b          	shr    $0x1b,%r8
  1a8189:	49 31 d0             	xor    %rdx,%r8
  1a818c:	4c 0f af c3          	imul   %rbx,%r8
  1a8190:	4c 89 c7             	mov    %r8,%rdi
  1a8193:	48 c1 ef 1f          	shr    $0x1f,%rdi
  1a8197:	4c 31 c7             	xor    %r8,%rdi
  1a819a:	49 89 f8             	mov    %rdi,%r8
  1a819d:	49 c1 e8 20          	shr    $0x20,%r8
  1a81a1:	4c 0f af c6          	imul   %rsi,%r8
  1a81a5:	49 c1 e8 20          	shr    $0x20,%r8
  1a81a9:	49 39 f0             	cmp    %rsi,%r8
  1a81ac:	0f 83 8a 00 00 00    	jae    1a823c <lanefilter::BlockedFilter::check_batch_lanes_masked+0x54c>
  1a81b2:	4c 39 f0             	cmp    %r14,%rax
  1a81b5:	73 6f                	jae    1a8226 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x536>
  1a81b7:	c5 f9 6e cf          	vmovd  %edi,%xmm1
  1a81bb:	c4 e2 7d 58 c9       	vpbroadcastd %xmm1,%ymm1
  1a81c0:	c4 e2 75 40 c8       	vpmulld %ymm0,%ymm1,%ymm1
  1a81c5:	49 c1 e0 05          	shl    $0x5,%r8
  1a81c9:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a81ce:	c4 81 7e 6f 14 03    	vmovdqu (%r11,%r8,1),%ymm2
  1a81d4:	c4 e2 6d 45 c9       	vpsrlvd %ymm1,%ymm2,%ymm1
  1a81d9:	c5 f5 72 f1 1f       	vpslld $0x1f,%ymm1,%ymm1
  1a81de:	c5 fc 50 d1          	vmovmskps %ymm1,%edx
  1a81e2:	81 fa ff 00 00 00    	cmp    $0xff,%edx
  1a81e8:	0f 94 04 01          	sete   (%rcx,%rax,1)
  1a81ec:	48 ff c0             	inc    %rax
  1a81ef:	49 83 c1 f8          	add    $0xfffffffffffffff8,%r9
  1a81f3:	0f 85 77 ff ff ff    	jne    1a8170 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x480>
  1a81f9:	48 83 c4 78          	add    $0x78,%rsp
  1a81fd:	5b                   	pop    %rbx
  1a81fe:	41 5c                	pop    %r12
  1a8200:	41 5d                	pop    %r13
  1a8202:	41 5e                	pop    %r14
  1a8204:	41 5f                	pop    %r15
  1a8206:	5d                   	pop    %rbp
  1a8207:	c5 f8 77             	vzeroupper
  1a820a:	c3                   	ret
  1a820b:	4c 8d 0d 7e 3d 0c 00 	lea    0xc3d7e(%rip),%r9        # 26bf90 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0x90>
  1a8212:	48 8d 74 24 20       	lea    0x20(%rsp),%rsi
  1a8217:	48 8d 54 24 28       	lea    0x28(%rsp),%rdx
  1a821c:	31 ff                	xor    %edi,%edi
  1a821e:	31 c9                	xor    %ecx,%ecx
  1a8220:	ff 15 62 9e 0c 00    	call   *0xc9e62(%rip)        # 272088 <_DYNAMIC+0x678>
  1a8226:	48 8d 15 7b 3d 0c 00 	lea    0xc3d7b(%rip),%rdx        # 26bfa8 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0xa8>
  1a822d:	48 89 c7             	mov    %rax,%rdi
  1a8230:	4c 89 f6             	mov    %r14,%rsi
  1a8233:	c5 f8 77             	vzeroupper
  1a8236:	ff 15 fc 99 0c 00    	call   *0xc99fc(%rip)        # 271c38 <_DYNAMIC+0x228>
  1a823c:	48 8d 15 95 3d 0c 00 	lea    0xc3d95(%rip),%rdx        # 26bfd8 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0xd8>
  1a8243:	4c 89 c7             	mov    %r8,%rdi
  1a8246:	c5 f8 77             	vzeroupper
  1a8249:	ff 15 e9 99 0c 00    	call   *0xc99e9(%rip)        # 271c38 <_DYNAMIC+0x228>
  1a824f:	4c 89 cf             	mov    %r9,%rdi
  1a8252:	45 84 d2             	test   %r10b,%r10b
  1a8255:	48 0f 45 fd          	cmovne %rbp,%rdi
  1a8259:	48 8d 15 60 3d 0c 00 	lea    0xc3d60(%rip),%rdx        # 26bfc0 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0xc0>
  1a8260:	c5 f8 77             	vzeroupper
  1a8263:	ff 15 cf 99 0c 00    	call   *0xc99cf(%rip)        # 271c38 <_DYNAMIC+0x228>
  1a8269:	49 39 f6             	cmp    %rsi,%r14
  1a826c:	4d 0f 43 fe          	cmovae %r14,%r15
  1a8270:	48 39 f3             	cmp    %rsi,%rbx
  1a8273:	4c 0f 43 fb          	cmovae %rbx,%r15
  1a8277:	49 39 f4             	cmp    %rsi,%r12
  1a827a:	4d 0f 43 ec          	cmovae %r12,%r13
  1a827e:	40 84 ed             	test   %bpl,%bpl
  1a8281:	4d 0f 45 ef          	cmovne %r15,%r13
  1a8285:	4c 89 ed             	mov    %r13,%rbp
  1a8288:	45 84 d2             	test   %r10b,%r10b
  1a828b:	48 0f 45 fd          	cmovne %rbp,%rdi
  1a828f:	48 8d 15 2a 3d 0c 00 	lea    0xc3d2a(%rip),%rdx        # 26bfc0 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0xc0>
  1a8296:	c5 f8 77             	vzeroupper
  1a8299:	ff 15 99 99 0c 00    	call   *0xc9999(%rip)        # 271c38 <_DYNAMIC+0x228>
  1a829f:	cc                   	int3

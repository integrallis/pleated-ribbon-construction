00000000001a76c0 <lanefilter::BlockedFilter::check_batch_lanes_masked>:
  1a76c0:	55                   	push   %rbp
  1a76c1:	41 57                	push   %r15
  1a76c3:	41 56                	push   %r14
  1a76c5:	41 55                	push   %r13
  1a76c7:	41 54                	push   %r12
  1a76c9:	53                   	push   %rbx
  1a76ca:	48 83 ec 78          	sub    $0x78,%rsp
  1a76ce:	48 89 3c 24          	mov    %rdi,(%rsp)
  1a76d2:	48 89 54 24 20       	mov    %rdx,0x20(%rsp)
  1a76d7:	4c 89 44 24 28       	mov    %r8,0x28(%rsp)
  1a76dc:	4c 39 c2             	cmp    %r8,%rdx
  1a76df:	0f 85 f6 04 00 00    	jne    1a7bdb <lanefilter::BlockedFilter::check_batch_lanes_masked+0x51b>
  1a76e5:	49 89 f7             	mov    %rsi,%r15
  1a76e8:	48 b8 f8 ff ff ff ff 	movabs $0xffffffffffffff8,%rax
  1a76ef:	ff ff 0f 
  1a76f2:	48 21 d0             	and    %rdx,%rax
  1a76f5:	48 89 54 24 08       	mov    %rdx,0x8(%rsp)
  1a76fa:	48 83 fa 08          	cmp    $0x8,%rdx
  1a76fe:	0f 82 f2 03 00 00    	jb     1a7af6 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x436>
  1a7704:	48 8b 14 24          	mov    (%rsp),%rdx
  1a7708:	4c 8b 42 08          	mov    0x8(%rdx),%r8
  1a770c:	48 8b 72 10          	mov    0x10(%rdx),%rsi
  1a7710:	c4 e1 f9 6e c6       	vmovq  %rsi,%xmm0
  1a7715:	c4 e2 7d 59 c0       	vpbroadcastq %xmm0,%ymm0
  1a771a:	c4 c1 f9 6e c9       	vmovq  %r9,%xmm1
  1a771f:	c4 e2 7d 59 c9       	vpbroadcastq %xmm1,%ymm1
  1a7724:	c5 fe 7f 4c 24 30    	vmovdqu %ymm1,0x30(%rsp)
  1a772a:	45 31 db             	xor    %r11d,%r11d
  1a772d:	c4 e2 7d 59 15 f2 3c 	vpbroadcastq -0x18c30e(%rip),%ymm2        # 1b428 <anon.1e953625a20d75503e29e94bdbca2956.1041.llvm.16250114296212024744+0x8>
  1a7734:	e7 ff 
  1a7736:	c4 e2 7d 59 1d b9 39 	vpbroadcastq -0x18c647(%rip),%ymm3        # 1b0f8 <anon.1e953625a20d75503e29e94bdbca2956.366.llvm.16250114296212024744+0x78>
  1a773d:	e7 ff 
  1a773f:	c4 e2 7d 59 25 e0 3b 	vpbroadcastq -0x18c420(%rip),%ymm4        # 1b328 <anon.052fb45616533950978e5170201c82f5.15.llvm.13389755735048657806+0x90>
  1a7746:	e7 ff 
  1a7748:	c4 e2 7d 59 2d bf 3c 	vpbroadcastq -0x18c341(%rip),%ymm5        # 1b410 <anon.3d721b55ae3f1027e4cd7f59e8b6b547.87.llvm.37457958396930264+0x70>
  1a774f:	e7 ff 
  1a7751:	c5 fe 7f 44 24 50    	vmovdqu %ymm0,0x50(%rsp)
  1a7757:	c5 cd 73 d0 20       	vpsrlq $0x20,%ymm0,%ymm6
  1a775c:	c5 fd 6f 3d 5c 34 e7 	vmovdqa -0x18cba4(%rip),%ymm7        # 1abc0 <anon.7701db75fdf4de9ca1078e4b56209abe.1.llvm.991980130354618317+0x2b8>
  1a7763:	ff 
  1a7764:	48 89 4c 24 18       	mov    %rcx,0x18(%rsp)
  1a7769:	4c 89 7c 24 10       	mov    %r15,0x10(%rsp)
  1a776e:	66 90                	xchg   %ax,%ax
  1a7770:	c4 01 7e 6f 04 df    	vmovdqu (%r15,%r11,8),%ymm8
  1a7776:	c4 01 7e 6f 4c df 20 	vmovdqu 0x20(%r15,%r11,8),%ymm9
  1a777d:	c4 c1 2d 73 d0 1e    	vpsrlq $0x1e,%ymm8,%ymm10
  1a7783:	c4 41 2d ef c0       	vpxor  %ymm8,%ymm10,%ymm8
  1a7788:	c5 3d f4 d2          	vpmuludq %ymm2,%ymm8,%ymm10
  1a778c:	c4 c1 25 73 d0 20    	vpsrlq $0x20,%ymm8,%ymm11
  1a7792:	c5 25 f4 db          	vpmuludq %ymm3,%ymm11,%ymm11
  1a7796:	c4 41 2d d4 d3       	vpaddq %ymm11,%ymm10,%ymm10
  1a779b:	c4 c1 2d 73 f2 20    	vpsllq $0x20,%ymm10,%ymm10
  1a77a1:	c5 3d f4 c3          	vpmuludq %ymm3,%ymm8,%ymm8
  1a77a5:	c4 41 3d d4 c2       	vpaddq %ymm10,%ymm8,%ymm8
  1a77aa:	c4 c1 2d 73 d0 1b    	vpsrlq $0x1b,%ymm8,%ymm10
  1a77b0:	c4 41 2d ef c0       	vpxor  %ymm8,%ymm10,%ymm8
  1a77b5:	c5 3d f4 d4          	vpmuludq %ymm4,%ymm8,%ymm10
  1a77b9:	c4 c1 25 73 d0 20    	vpsrlq $0x20,%ymm8,%ymm11
  1a77bf:	c5 25 f4 dd          	vpmuludq %ymm5,%ymm11,%ymm11
  1a77c3:	c4 41 2d d4 d3       	vpaddq %ymm11,%ymm10,%ymm10
  1a77c8:	c4 c1 2d 73 f2 20    	vpsllq $0x20,%ymm10,%ymm10
  1a77ce:	c5 3d f4 c5          	vpmuludq %ymm5,%ymm8,%ymm8
  1a77d2:	c4 41 3d d4 c2       	vpaddq %ymm10,%ymm8,%ymm8
  1a77d7:	c4 c1 2d 73 d0 1f    	vpsrlq $0x1f,%ymm8,%ymm10
  1a77dd:	c4 41 2d ef d0       	vpxor  %ymm8,%ymm10,%ymm10
  1a77e2:	c4 c1 3d 73 d2 20    	vpsrlq $0x20,%ymm10,%ymm8
  1a77e8:	c5 fe 6f 44 24 50    	vmovdqu 0x50(%rsp),%ymm0
  1a77ee:	c5 3d f4 d8          	vpmuludq %ymm0,%ymm8,%ymm11
  1a77f2:	c5 3d f4 c6          	vpmuludq %ymm6,%ymm8,%ymm8
  1a77f6:	c4 c1 3d 73 f0 20    	vpsllq $0x20,%ymm8,%ymm8
  1a77fc:	c4 41 25 d4 c0       	vpaddq %ymm8,%ymm11,%ymm8
  1a7801:	c4 c1 3d 73 d0 20    	vpsrlq $0x20,%ymm8,%ymm8
  1a7807:	c5 fe 6f 4c 24 30    	vmovdqu 0x30(%rsp),%ymm1
  1a780d:	c5 3d db c1          	vpand  %ymm1,%ymm8,%ymm8
  1a7811:	c4 c1 25 73 d1 1e    	vpsrlq $0x1e,%ymm9,%ymm11
  1a7817:	c4 41 25 ef c9       	vpxor  %ymm9,%ymm11,%ymm9
  1a781c:	c5 35 f4 da          	vpmuludq %ymm2,%ymm9,%ymm11
  1a7820:	c4 c1 1d 73 d1 20    	vpsrlq $0x20,%ymm9,%ymm12
  1a7826:	c5 1d f4 e3          	vpmuludq %ymm3,%ymm12,%ymm12
  1a782a:	c4 41 25 d4 dc       	vpaddq %ymm12,%ymm11,%ymm11
  1a782f:	c4 c1 25 73 f3 20    	vpsllq $0x20,%ymm11,%ymm11
  1a7835:	c5 35 f4 cb          	vpmuludq %ymm3,%ymm9,%ymm9
  1a7839:	c4 41 35 d4 cb       	vpaddq %ymm11,%ymm9,%ymm9
  1a783e:	c4 c1 25 73 d1 1b    	vpsrlq $0x1b,%ymm9,%ymm11
  1a7844:	c4 41 25 ef c9       	vpxor  %ymm9,%ymm11,%ymm9
  1a7849:	c5 35 f4 dc          	vpmuludq %ymm4,%ymm9,%ymm11
  1a784d:	c4 c1 1d 73 d1 20    	vpsrlq $0x20,%ymm9,%ymm12
  1a7853:	c5 1d f4 e5          	vpmuludq %ymm5,%ymm12,%ymm12
  1a7857:	c4 41 25 d4 dc       	vpaddq %ymm12,%ymm11,%ymm11
  1a785c:	c4 c1 25 73 f3 20    	vpsllq $0x20,%ymm11,%ymm11
  1a7862:	c5 35 f4 cd          	vpmuludq %ymm5,%ymm9,%ymm9
  1a7866:	c4 41 35 d4 cb       	vpaddq %ymm11,%ymm9,%ymm9
  1a786b:	c4 c1 25 73 d1 1f    	vpsrlq $0x1f,%ymm9,%ymm11
  1a7871:	c4 41 25 ef d9       	vpxor  %ymm9,%ymm11,%ymm11
  1a7876:	c4 c1 35 73 d3 20    	vpsrlq $0x20,%ymm11,%ymm9
  1a787c:	c5 35 f4 e0          	vpmuludq %ymm0,%ymm9,%ymm12
  1a7880:	c5 35 f4 ce          	vpmuludq %ymm6,%ymm9,%ymm9
  1a7884:	c4 c1 35 73 f1 20    	vpsllq $0x20,%ymm9,%ymm9
  1a788a:	c4 41 1d d4 c9       	vpaddq %ymm9,%ymm12,%ymm9
  1a788f:	c4 c1 35 73 d1 20    	vpsrlq $0x20,%ymm9,%ymm9
  1a7895:	c4 61 f9 7e c3       	vmovq  %xmm8,%rbx
  1a789a:	48 39 f3             	cmp    %rsi,%rbx
  1a789d:	41 0f 93 c1          	setae  %r9b
  1a78a1:	c4 43 f9 16 c6 01    	vpextrq $0x1,%xmm8,%r14
  1a78a7:	c5 35 db c9          	vpand  %ymm1,%ymm9,%ymm9
  1a78ab:	49 39 f6             	cmp    %rsi,%r14
  1a78ae:	40 0f 93 c5          	setae  %bpl
  1a78b2:	c4 43 7d 39 c0 01    	vextracti128 $0x1,%ymm8,%xmm8
  1a78b8:	c4 41 f9 7e c7       	vmovq  %xmm8,%r15
  1a78bd:	49 39 f7             	cmp    %rsi,%r15
  1a78c0:	0f 93 c2             	setae  %dl
  1a78c3:	c4 43 f9 16 c4 01    	vpextrq $0x1,%xmm8,%r12
  1a78c9:	49 39 f4             	cmp    %rsi,%r12
  1a78cc:	0f 93 c1             	setae  %cl
  1a78cf:	c4 41 f9 7e cd       	vmovq  %xmm9,%r13
  1a78d4:	49 39 f5             	cmp    %rsi,%r13
  1a78d7:	41 0f 93 c2          	setae  %r10b
  1a78db:	c4 63 f9 16 cf 01    	vpextrq $0x1,%xmm9,%rdi
  1a78e1:	44 08 cd             	or     %r9b,%bpl
  1a78e4:	40 08 d5             	or     %dl,%bpl
  1a78e7:	41 08 ca             	or     %cl,%r10b
  1a78ea:	41 08 ea             	or     %bpl,%r10b
  1a78ed:	0f 85 46 03 00 00    	jne    1a7c39 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x579>
  1a78f3:	48 39 f7             	cmp    %rsi,%rdi
  1a78f6:	0f 83 3d 03 00 00    	jae    1a7c39 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x579>
  1a78fc:	c4 43 7d 39 c8 01    	vextracti128 $0x1,%ymm9,%xmm8
  1a7902:	c4 61 f9 7e c5       	vmovq  %xmm8,%rbp
  1a7907:	c4 43 f9 16 c1 01    	vpextrq $0x1,%xmm8,%r9
  1a790d:	48 39 f5             	cmp    %rsi,%rbp
  1a7910:	41 0f 93 c2          	setae  %r10b
  1a7914:	0f 83 05 03 00 00    	jae    1a7c1f <lanefilter::BlockedFilter::check_batch_lanes_masked+0x55f>
  1a791a:	49 39 f1             	cmp    %rsi,%r9
  1a791d:	0f 83 fc 02 00 00    	jae    1a7c1f <lanefilter::BlockedFilter::check_batch_lanes_masked+0x55f>
  1a7923:	c4 42 7d 58 e2       	vpbroadcastd %xmm10,%ymm12
  1a7928:	c4 62 7d 58 05 43 23 	vpbroadcastd -0x18dcbd(%rip),%ymm8        # 19c74 <anon.1e953625a20d75503e29e94bdbca2956.583.llvm.16250114296212024744+0x30>
  1a792f:	e7 ff 
  1a7931:	c4 42 3d 36 ea       	vpermd %ymm10,%ymm8,%ymm13
  1a7936:	c4 62 7d 58 3d 91 22 	vpbroadcastd -0x18dd6f(%rip),%ymm15        # 19bd0 <anon.3d721b55ae3f1027e4cd7f59e8b6b547.85.llvm.37457958396930264+0x10>
  1a793d:	e7 ff 
  1a793f:	c4 42 05 36 f2       	vpermd %ymm10,%ymm15,%ymm14
  1a7944:	c4 e2 7d 58 0d 4b 23 	vpbroadcastd -0x18dcb5(%rip),%ymm1        # 19c98 <anon.566e8472f54db27c7ffa65d7a5411555.7.llvm.6122657087698423557+0x8>
  1a794b:	e7 ff 
  1a794d:	c4 41 30 57 c9       	vxorps %xmm9,%xmm9,%xmm9
  1a7952:	c4 42 75 36 ca       	vpermd %ymm10,%ymm1,%ymm9
  1a7957:	c4 c2 7d 58 c3       	vpbroadcastd %xmm11,%ymm0
  1a795c:	c4 42 3d 36 c3       	vpermd %ymm11,%ymm8,%ymm8
  1a7961:	c4 42 05 36 fb       	vpermd %ymm11,%ymm15,%ymm15
  1a7966:	c4 c2 75 36 cb       	vpermd %ymm11,%ymm1,%ymm1
  1a796b:	49 c1 e1 05          	shl    $0x5,%r9
  1a796f:	c4 e2 75 40 cf       	vpmulld %ymm7,%ymm1,%ymm1
  1a7974:	c4 01 7e 6f 14 08    	vmovdqu (%r8,%r9,1),%ymm10
  1a797a:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a797f:	c4 62 2d 45 d1       	vpsrlvd %ymm1,%ymm10,%ymm10
  1a7984:	48 c1 e5 05          	shl    $0x5,%rbp
  1a7988:	c4 e2 05 40 cf       	vpmulld %ymm7,%ymm15,%ymm1
  1a798d:	c4 41 7e 6f 1c 28    	vmovdqu (%r8,%rbp,1),%ymm11
  1a7993:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a7998:	c4 62 25 45 d9       	vpsrlvd %ymm1,%ymm11,%ymm11
  1a799d:	48 c1 e7 05          	shl    $0x5,%rdi
  1a79a1:	c4 e2 3d 40 cf       	vpmulld %ymm7,%ymm8,%ymm1
  1a79a6:	c4 41 7e 6f 04 38    	vmovdqu (%r8,%rdi,1),%ymm8
  1a79ac:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a79b1:	c4 62 3d 45 f9       	vpsrlvd %ymm1,%ymm8,%ymm15
  1a79b6:	49 c1 e5 05          	shl    $0x5,%r13
  1a79ba:	c4 e2 7d 40 c7       	vpmulld %ymm7,%ymm0,%ymm0
  1a79bf:	c4 81 7e 6f 0c 28    	vmovdqu (%r8,%r13,1),%ymm1
  1a79c5:	c5 fd 72 d0 1b       	vpsrld $0x1b,%ymm0,%ymm0
  1a79ca:	c4 62 75 45 c0       	vpsrlvd %ymm0,%ymm1,%ymm8
  1a79cf:	49 c1 e4 05          	shl    $0x5,%r12
  1a79d3:	c4 e2 35 40 c7       	vpmulld %ymm7,%ymm9,%ymm0
  1a79d8:	c4 81 7e 6f 0c 20    	vmovdqu (%r8,%r12,1),%ymm1
  1a79de:	c5 fd 72 d0 1b       	vpsrld $0x1b,%ymm0,%ymm0
  1a79e3:	c4 62 75 45 c8       	vpsrlvd %ymm0,%ymm1,%ymm9
  1a79e8:	49 c1 e7 05          	shl    $0x5,%r15
  1a79ec:	c4 e2 0d 40 c7       	vpmulld %ymm7,%ymm14,%ymm0
  1a79f1:	c4 81 7e 6f 0c 38    	vmovdqu (%r8,%r15,1),%ymm1
  1a79f7:	c5 fd 72 d0 1b       	vpsrld $0x1b,%ymm0,%ymm0
  1a79fc:	c4 62 75 45 f0       	vpsrlvd %ymm0,%ymm1,%ymm14
  1a7a01:	49 c1 e6 05          	shl    $0x5,%r14
  1a7a05:	c4 e2 15 40 c7       	vpmulld %ymm7,%ymm13,%ymm0
  1a7a0a:	c4 81 7e 6f 0c 30    	vmovdqu (%r8,%r14,1),%ymm1
  1a7a10:	c5 fd 72 d0 1b       	vpsrld $0x1b,%ymm0,%ymm0
  1a7a15:	c4 e2 75 45 c0       	vpsrlvd %ymm0,%ymm1,%ymm0
  1a7a1a:	c4 e2 1d 40 cf       	vpmulld %ymm7,%ymm12,%ymm1
  1a7a1f:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a7a24:	48 c1 e3 05          	shl    $0x5,%rbx
  1a7a28:	c4 41 7e 6f 24 18    	vmovdqu (%r8,%rbx,1),%ymm12
  1a7a2e:	c4 e2 1d 45 c9       	vpsrlvd %ymm1,%ymm12,%ymm1
  1a7a33:	c4 c1 2d 72 f2 1f    	vpslld $0x1f,%ymm10,%ymm10
  1a7a39:	c4 41 7c 50 ca       	vmovmskps %ymm10,%r9d
  1a7a3e:	41 f7 d1             	not    %r9d
  1a7a41:	c4 c1 2d 72 f3 1f    	vpslld $0x1f,%ymm11,%ymm10
  1a7a47:	c4 41 7c 50 d2       	vmovmskps %ymm10,%r10d
  1a7a4c:	41 f7 d2             	not    %r10d
  1a7a4f:	c4 c1 2d 72 f7 1f    	vpslld $0x1f,%ymm15,%ymm10
  1a7a55:	c4 c1 7c 50 ca       	vmovmskps %ymm10,%ecx
  1a7a5a:	f7 d1                	not    %ecx
  1a7a5c:	c4 c1 3d 72 f0 1f    	vpslld $0x1f,%ymm8,%ymm8
  1a7a62:	c4 c1 7c 50 d0       	vmovmskps %ymm8,%edx
  1a7a67:	f7 d2                	not    %edx
  1a7a69:	c4 c1 3d 72 f1 1f    	vpslld $0x1f,%ymm9,%ymm8
  1a7a6f:	c4 c1 7c 50 f8       	vmovmskps %ymm8,%edi
  1a7a74:	f7 d7                	not    %edi
  1a7a76:	c4 c1 3d 72 f6 1f    	vpslld $0x1f,%ymm14,%ymm8
  1a7a7c:	c4 c1 7c 50 d8       	vmovmskps %ymm8,%ebx
  1a7a81:	f7 d3                	not    %ebx
  1a7a83:	c5 fd 72 f0 1f       	vpslld $0x1f,%ymm0,%ymm0
  1a7a88:	c5 fc 50 e8          	vmovmskps %ymm0,%ebp
  1a7a8c:	f7 d5                	not    %ebp
  1a7a8e:	c5 fd 72 f1 1f       	vpslld $0x1f,%ymm1,%ymm0
  1a7a93:	c5 7c 50 f0          	vmovmskps %ymm0,%r14d
  1a7a97:	41 f7 d6             	not    %r14d
  1a7a9a:	c4 c1 79 6e c6       	vmovd  %r14d,%xmm0
  1a7a9f:	c4 e3 79 20 c5 01    	vpinsrb $0x1,%ebp,%xmm0,%xmm0
  1a7aa5:	c4 e3 79 20 c3 02    	vpinsrb $0x2,%ebx,%xmm0,%xmm0
  1a7aab:	c4 e3 79 20 c7 03    	vpinsrb $0x3,%edi,%xmm0,%xmm0
  1a7ab1:	c4 e3 79 20 c2 04    	vpinsrb $0x4,%edx,%xmm0,%xmm0
  1a7ab7:	c4 e3 79 20 c1 05    	vpinsrb $0x5,%ecx,%xmm0,%xmm0
  1a7abd:	c4 c3 79 20 c2 06    	vpinsrb $0x6,%r10d,%xmm0,%xmm0
  1a7ac3:	c4 c3 79 20 c1 07    	vpinsrb $0x7,%r9d,%xmm0,%xmm0
  1a7ac9:	c5 f1 ef c9          	vpxor  %xmm1,%xmm1,%xmm1
  1a7acd:	c5 f9 74 c1          	vpcmpeqb %xmm1,%xmm0,%xmm0
  1a7ad1:	c5 f9 db 05 17 23 e7 	vpand  -0x18dce9(%rip),%xmm0,%xmm0        # 19df0 <anon.052fb45616533950978e5170201c82f5.13.llvm.13389755735048657806+0xec>
  1a7ad8:	ff 
  1a7ad9:	48 8b 4c 24 18       	mov    0x18(%rsp),%rcx
  1a7ade:	c4 a1 79 d6 04 19    	vmovq  %xmm0,(%rcx,%r11,1)
  1a7ae4:	49 83 c3 08          	add    $0x8,%r11
  1a7ae8:	4c 39 d8             	cmp    %r11,%rax
  1a7aeb:	4c 8b 7c 24 10       	mov    0x10(%rsp),%r15
  1a7af0:	0f 85 7a fc ff ff    	jne    1a7770 <lanefilter::BlockedFilter::check_batch_lanes_masked+0xb0>
  1a7af6:	4c 8b 74 24 08       	mov    0x8(%rsp),%r14
  1a7afb:	46 8d 0c f5 00 00 00 	lea    0x0(,%r14,8),%r9d
  1a7b02:	00 
  1a7b03:	41 83 e1 38          	and    $0x38,%r9d
  1a7b07:	0f 84 bc 00 00 00    	je     1a7bc9 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x509>
  1a7b0d:	48 8b 14 24          	mov    (%rsp),%rdx
  1a7b11:	4c 8b 5a 08          	mov    0x8(%rdx),%r11
  1a7b15:	48 8b 72 10          	mov    0x10(%rdx),%rsi
  1a7b19:	49 ba b9 e5 e4 1c 6d 	movabs $0xbf58476d1ce4e5b9,%r10
  1a7b20:	47 58 bf 
  1a7b23:	48 bb eb 11 31 13 bb 	movabs $0x94d049bb133111eb,%rbx
  1a7b2a:	49 d0 94 
  1a7b2d:	c5 fd 6f 05 8b 30 e7 	vmovdqa -0x18cf75(%rip),%ymm0        # 1abc0 <anon.7701db75fdf4de9ca1078e4b56209abe.1.llvm.991980130354618317+0x2b8>
  1a7b34:	ff 
  1a7b35:	66 66 2e 0f 1f 84 00 	data16 cs nopw 0x0(%rax,%rax,1)
  1a7b3c:	00 00 00 00 
  1a7b40:	49 8b 3c c7          	mov    (%r15,%rax,8),%rdi
  1a7b44:	48 89 fa             	mov    %rdi,%rdx
  1a7b47:	48 c1 ea 1e          	shr    $0x1e,%rdx
  1a7b4b:	48 31 fa             	xor    %rdi,%rdx
  1a7b4e:	49 0f af d2          	imul   %r10,%rdx
  1a7b52:	49 89 d0             	mov    %rdx,%r8
  1a7b55:	49 c1 e8 1b          	shr    $0x1b,%r8
  1a7b59:	49 31 d0             	xor    %rdx,%r8
  1a7b5c:	4c 0f af c3          	imul   %rbx,%r8
  1a7b60:	4c 89 c7             	mov    %r8,%rdi
  1a7b63:	48 c1 ef 1f          	shr    $0x1f,%rdi
  1a7b67:	4c 31 c7             	xor    %r8,%rdi
  1a7b6a:	49 89 f8             	mov    %rdi,%r8
  1a7b6d:	49 c1 e8 20          	shr    $0x20,%r8
  1a7b71:	4c 0f af c6          	imul   %rsi,%r8
  1a7b75:	49 c1 e8 20          	shr    $0x20,%r8
  1a7b79:	49 39 f0             	cmp    %rsi,%r8
  1a7b7c:	0f 83 8a 00 00 00    	jae    1a7c0c <lanefilter::BlockedFilter::check_batch_lanes_masked+0x54c>
  1a7b82:	4c 39 f0             	cmp    %r14,%rax
  1a7b85:	73 6f                	jae    1a7bf6 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x536>
  1a7b87:	c5 f9 6e cf          	vmovd  %edi,%xmm1
  1a7b8b:	c4 e2 7d 58 c9       	vpbroadcastd %xmm1,%ymm1
  1a7b90:	c4 e2 75 40 c8       	vpmulld %ymm0,%ymm1,%ymm1
  1a7b95:	49 c1 e0 05          	shl    $0x5,%r8
  1a7b99:	c5 f5 72 d1 1b       	vpsrld $0x1b,%ymm1,%ymm1
  1a7b9e:	c4 81 7e 6f 14 03    	vmovdqu (%r11,%r8,1),%ymm2
  1a7ba4:	c4 e2 6d 45 c9       	vpsrlvd %ymm1,%ymm2,%ymm1
  1a7ba9:	c5 f5 72 f1 1f       	vpslld $0x1f,%ymm1,%ymm1
  1a7bae:	c5 fc 50 d1          	vmovmskps %ymm1,%edx
  1a7bb2:	81 fa ff 00 00 00    	cmp    $0xff,%edx
  1a7bb8:	0f 94 04 01          	sete   (%rcx,%rax,1)
  1a7bbc:	48 ff c0             	inc    %rax
  1a7bbf:	49 83 c1 f8          	add    $0xfffffffffffffff8,%r9
  1a7bc3:	0f 85 77 ff ff ff    	jne    1a7b40 <lanefilter::BlockedFilter::check_batch_lanes_masked+0x480>
  1a7bc9:	48 83 c4 78          	add    $0x78,%rsp
  1a7bcd:	5b                   	pop    %rbx
  1a7bce:	41 5c                	pop    %r12
  1a7bd0:	41 5d                	pop    %r13
  1a7bd2:	41 5e                	pop    %r14
  1a7bd4:	41 5f                	pop    %r15
  1a7bd6:	5d                   	pop    %rbp
  1a7bd7:	c5 f8 77             	vzeroupper
  1a7bda:	c3                   	ret
  1a7bdb:	4c 8d 0d 06 3d 0c 00 	lea    0xc3d06(%rip),%r9        # 26b8e8 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0x90>
  1a7be2:	48 8d 74 24 20       	lea    0x20(%rsp),%rsi
  1a7be7:	48 8d 54 24 28       	lea    0x28(%rsp),%rdx
  1a7bec:	31 ff                	xor    %edi,%edi
  1a7bee:	31 c9                	xor    %ecx,%ecx
  1a7bf0:	ff 15 ea 9d 0c 00    	call   *0xc9dea(%rip)        # 2719e0 <_DYNAMIC+0x678>
  1a7bf6:	48 8d 15 03 3d 0c 00 	lea    0xc3d03(%rip),%rdx        # 26b900 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0xa8>
  1a7bfd:	48 89 c7             	mov    %rax,%rdi
  1a7c00:	4c 89 f6             	mov    %r14,%rsi
  1a7c03:	c5 f8 77             	vzeroupper
  1a7c06:	ff 15 84 99 0c 00    	call   *0xc9984(%rip)        # 271590 <_DYNAMIC+0x228>
  1a7c0c:	48 8d 15 1d 3d 0c 00 	lea    0xc3d1d(%rip),%rdx        # 26b930 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0xd8>
  1a7c13:	4c 89 c7             	mov    %r8,%rdi
  1a7c16:	c5 f8 77             	vzeroupper
  1a7c19:	ff 15 71 99 0c 00    	call   *0xc9971(%rip)        # 271590 <_DYNAMIC+0x228>
  1a7c1f:	4c 89 cf             	mov    %r9,%rdi
  1a7c22:	45 84 d2             	test   %r10b,%r10b
  1a7c25:	48 0f 45 fd          	cmovne %rbp,%rdi
  1a7c29:	48 8d 15 e8 3c 0c 00 	lea    0xc3ce8(%rip),%rdx        # 26b918 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0xc0>
  1a7c30:	c5 f8 77             	vzeroupper
  1a7c33:	ff 15 57 99 0c 00    	call   *0xc9957(%rip)        # 271590 <_DYNAMIC+0x228>
  1a7c39:	49 39 f6             	cmp    %rsi,%r14
  1a7c3c:	4d 0f 43 fe          	cmovae %r14,%r15
  1a7c40:	48 39 f3             	cmp    %rsi,%rbx
  1a7c43:	4c 0f 43 fb          	cmovae %rbx,%r15
  1a7c47:	49 39 f4             	cmp    %rsi,%r12
  1a7c4a:	4d 0f 43 ec          	cmovae %r12,%r13
  1a7c4e:	40 84 ed             	test   %bpl,%bpl
  1a7c51:	4d 0f 45 ef          	cmovne %r15,%r13
  1a7c55:	4c 89 ed             	mov    %r13,%rbp
  1a7c58:	45 84 d2             	test   %r10b,%r10b
  1a7c5b:	48 0f 45 fd          	cmovne %rbp,%rdi
  1a7c5f:	48 8d 15 b2 3c 0c 00 	lea    0xc3cb2(%rip),%rdx        # 26b918 <anon.bd7cca4170763bed7e785b31278d1c53.7.llvm.1470931581427472828+0xc0>
  1a7c66:	c5 f8 77             	vzeroupper
  1a7c69:	ff 15 21 99 0c 00    	call   *0xc9921(%rip)        # 271590 <_DYNAMIC+0x228>
  1a7c6f:	cc                   	int3

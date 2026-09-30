000000000010f080 <<lanefilter::BlockedFilter>::check_batch_lanes_masked>:
  10f080:	d101c3ff 	sub	sp, sp, #0x70
  10f084:	a9017bfd 	stp	x29, x30, [sp, #16]
  10f088:	f90013fb 	str	x27, [sp, #32]
  10f08c:	a90367fa 	stp	x26, x25, [sp, #48]
  10f090:	a9045ff8 	stp	x24, x23, [sp, #64]
  10f094:	a90557f6 	stp	x22, x21, [sp, #80]
  10f098:	a9064ff4 	stp	x20, x19, [sp, #96]
  10f09c:	910043fd 	add	x29, sp, #0x10
  10f0a0:	f90007e2 	str	x2, [sp, #8]
  10f0a4:	f9000fa4 	str	x4, [x29, #24]
  10f0a8:	eb04005f 	cmp	x2, x4
  10f0ac:	540049a1 	b.ne	10f9e0 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x960>  // b.any
  10f0b0:	d29cb72b 	mov	x11, #0xe5b9                	// #58809
  10f0b4:	d2823d6a 	mov	x10, #0x11eb                	// #4587
  10f0b8:	d343fc49 	lsr	x9, x2, #3
  10f0bc:	aa0103e8 	mov	x8, x1
  10f0c0:	f2a39c8b 	movk	x11, #0x1ce4, lsl #16
  10f0c4:	f2a2662a 	movk	x10, #0x1331, lsl #16
  10f0c8:	f2c8edab 	movk	x11, #0x476d, lsl #32
  10f0cc:	f2c9376a 	movk	x10, #0x49bb, lsl #32
  10f0d0:	f2f7eb0b 	movk	x11, #0xbf58, lsl #48
  10f0d4:	f2f29a0a 	movk	x10, #0x94d0, lsl #48
  10f0d8:	b4002249 	cbz	x9, 10f520 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x4a0>
  10f0dc:	2558e025 	ptrue	p5.h, vl1
  10f0e0:	2578c025 	mov	z5.h, #1
  10f0e4:	52800030 	mov	w16, #0x1                   	// #1
  10f0e8:	a940840c 	ldp	x12, x1, [x0, #8]
  10f0ec:	2558e3e0 	ptrue	p0.h
  10f0f0:	2558e103 	ptrue	p3.h, vl8
  10f0f4:	4e080ca1 	dup	v1.2d, x5
  10f0f8:	25b8c024 	mov	z4.s, #1
  10f0fc:	91000c6d 	add	x13, x3, #0x3
  10f100:	9100810e 	add	x14, x8, #0x20
  10f104:	f000056f 	adrp	x15, 1be000 <anon.e409443c481834e9ae3b5da2c9a3400d.0.llvm.9106801964020432495+0x128>
  10f108:	910901ef 	add	x15, x15, #0x240
  10f10c:	0568b605 	mov	z5.h, p5/m, w16
  10f110:	4e080d62 	dup	v2.2d, x11
  10f114:	05800405 	and	z5.h, z5.h, #0x1
  10f118:	4e080c20 	dup	v0.2d, x1
  10f11c:	4e080d43 	dup	v3.2d, x10
  10f120:	25004261 	not	p1.b, p0/z, p3.b
  10f124:	05304062 	punpklo	p2.h, p3.b
  10f128:	05314063 	punpkhi	p3.h, p3.b
  10f12c:	2598e3e4 	ptrue	p4.s
  10f130:	254080b5 	cmpne	p5.h, p0/z, z5.h, #0
  10f134:	d503201f 	nop
  10f138:	d503201f 	nop
  10f13c:	d503201f 	nop
  10f140:	ad7f19c5 	ldp	q5, q6, [x14, #-32]
  10f144:	6f6204d0 	ushr	v16.2d, v6.2d, #30
  10f148:	6f6204a7 	ushr	v7.2d, v5.2d, #30
  10f14c:	6e261e06 	eor	v6.16b, v16.16b, v6.16b
  10f150:	6e251ce5 	eor	v5.16b, v7.16b, v5.16b
  10f154:	04e260c6 	mul	z6.d, z6.d, z2.d
  10f158:	04e260a5 	mul	z5.d, z5.d, z2.d
  10f15c:	6f6504d0 	ushr	v16.2d, v6.2d, #27
  10f160:	6f6504a7 	ushr	v7.2d, v5.2d, #27
  10f164:	6e261e06 	eor	v6.16b, v16.16b, v6.16b
  10f168:	6e251ce5 	eor	v5.16b, v7.16b, v5.16b
  10f16c:	04e360c6 	mul	z6.d, z6.d, z3.d
  10f170:	6f6104d0 	ushr	v16.2d, v6.2d, #31
  10f174:	04e360a5 	mul	z5.d, z5.d, z3.d
  10f178:	6f6104a7 	ushr	v7.2d, v5.2d, #31
  10f17c:	6e261e06 	eor	v6.16b, v16.16b, v6.16b
  10f180:	6e251ce5 	eor	v5.16b, v7.16b, v5.16b
  10f184:	6f6004d0 	ushr	v16.2d, v6.2d, #32
  10f188:	6f6004a7 	ushr	v7.2d, v5.2d, #32
  10f18c:	04e06210 	mul	z16.d, z16.d, z0.d
  10f190:	04e060e7 	mul	z7.d, z7.d, z0.d
  10f194:	6f6004e7 	ushr	v7.2d, v7.2d, #32
  10f198:	4e211cf1 	and	v17.16b, v7.16b, v1.16b
  10f19c:	6f600607 	ushr	v7.2d, v16.2d, #32
  10f1a0:	4e211cf0 	and	v16.16b, v7.16b, v1.16b
  10f1a4:	3dc001c7 	ldr	q7, [x14]
  10f1a8:	9e660227 	fmov	x7, d17
  10f1ac:	4e183e33 	mov	x19, v17.d[1]
  10f1b0:	eb0100ff 	cmp	x7, x1
  10f1b4:	9e660214 	fmov	x20, d16
  10f1b8:	fa413262 	ccmp	x19, x1, #0x2, cc	// cc = lo, ul, last
  10f1bc:	4e183e06 	mov	x6, v16.d[1]
  10f1c0:	fa413282 	ccmp	x20, x1, #0x2, cc	// cc = lo, ul, last
  10f1c4:	1a9f37f1 	cset	w17, cs	// cs = hs, nlast
  10f1c8:	eb0100df 	cmp	x6, x1
  10f1cc:	6f6204f2 	ushr	v18.2d, v7.2d, #30
  10f1d0:	1a9f3632 	csinc	w18, w17, wzr, cc	// cc = lo, ul, last
  10f1d4:	6e271e47 	eor	v7.16b, v18.16b, v7.16b
  10f1d8:	04e260e7 	mul	z7.d, z7.d, z2.d
  10f1dc:	6f6504f2 	ushr	v18.2d, v7.2d, #27
  10f1e0:	6e271e47 	eor	v7.16b, v18.16b, v7.16b
  10f1e4:	04e360e7 	mul	z7.d, z7.d, z3.d
  10f1e8:	6f6104f2 	ushr	v18.2d, v7.2d, #31
  10f1ec:	6e271e47 	eor	v7.16b, v18.16b, v7.16b
  10f1f0:	6f6004f2 	ushr	v18.2d, v7.2d, #32
  10f1f4:	04e06252 	mul	z18.d, z18.d, z0.d
  10f1f8:	6f600652 	ushr	v18.2d, v18.2d, #32
  10f1fc:	4e211e52 	and	v18.16b, v18.16b, v1.16b
  10f200:	9e660244 	fmov	x4, d18
  10f204:	4e183e50 	mov	x16, v18.d[1]
  10f208:	eb01009f 	cmp	x4, x1
  10f20c:	1a9f3645 	csinc	w5, w18, wzr, cc	// cc = lo, ul, last
  10f210:	37003f65 	tbnz	w5, #0, 10f9fc <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x97c>
  10f214:	eb01021f 	cmp	x16, x1
  10f218:	54003f22 	b.cs	10f9fc <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x97c>  // b.hs, b.nlast
  10f21c:	3dc005d0 	ldr	q16, [x14, #16]
  10f220:	6f620611 	ushr	v17.2d, v16.2d, #30
  10f224:	6e301e30 	eor	v16.16b, v17.16b, v16.16b
  10f228:	04e26210 	mul	z16.d, z16.d, z2.d
  10f22c:	6f650611 	ushr	v17.2d, v16.2d, #27
  10f230:	6e301e30 	eor	v16.16b, v17.16b, v16.16b
  10f234:	04e36210 	mul	z16.d, z16.d, z3.d
  10f238:	6f610611 	ushr	v17.2d, v16.2d, #31
  10f23c:	6e301e30 	eor	v16.16b, v17.16b, v16.16b
  10f240:	6f600611 	ushr	v17.2d, v16.2d, #32
  10f244:	04e06231 	mul	z17.d, z17.d, z0.d
  10f248:	6f600631 	ushr	v17.2d, v17.2d, #32
  10f24c:	4e211e31 	and	v17.16b, v17.16b, v1.16b
  10f250:	9e660232 	fmov	x18, d17
  10f254:	4e183e31 	mov	x17, v17.d[1]
  10f258:	eb01025f 	cmp	x18, x1
  10f25c:	1a9f37e5 	cset	w5, cs	// cs = hs, nlast
  10f260:	fa413222 	ccmp	x17, x1, #0x2, cc	// cc = lo, ul, last
  10f264:	54003e62 	b.cs	10fa30 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9b0>  // b.hs, b.nlast
  10f268:	1e2600b5 	fmov	w21, s5
  10f26c:	8b071587 	add	x7, x12, x7, lsl #5
  10f270:	8b131593 	add	x19, x12, x19, lsl #5
  10f274:	8b141594 	add	x20, x12, x20, lsl #5
  10f278:	910101ce 	add	x14, x14, #0x40
  10f27c:	0e143cb6 	mov	w22, v5.s[2]
  10f280:	a540a9e5 	ld1w	{z5.s}, p2/z, [x15]
  10f284:	8b061586 	add	x6, x12, x6, lsl #5
  10f288:	8b041584 	add	x4, x12, x4, lsl #5
  10f28c:	a541acf7 	ld1w	{z23.s}, p3/z, [x7, #1, mul vl]
  10f290:	1e2600d7 	fmov	w23, s6
  10f294:	05a03ab3 	mov	z19.s, w21
  10f298:	a540a8f8 	ld1w	{z24.s}, p2/z, [x7]
  10f29c:	05a03ad4 	mov	z20.s, w22
  10f2a0:	05a03af5 	mov	z21.s, w23
  10f2a4:	0e143cd8 	mov	w24, v6.s[2]
  10f2a8:	a541ade6 	ld1w	{z6.s}, p3/z, [x15, #1, mul vl]
  10f2ac:	1e2600f9 	fmov	w25, s7
  10f2b0:	05a03b12 	mov	z18.s, w24
  10f2b4:	05a03b31 	mov	z17.s, w25
  10f2b8:	8b101590 	add	x16, x12, x16, lsl #5
  10f2bc:	0e143cfa 	mov	w26, v7.s[2]
  10f2c0:	8b121592 	add	x18, x12, x18, lsl #5
  10f2c4:	8b111591 	add	x17, x12, x17, lsl #5
  10f2c8:	1e26021b 	fmov	w27, s16
  10f2cc:	05a03b67 	mov	z7.s, w27
  10f2d0:	04b360d6 	mul	z22.s, z6.s, z19.s
  10f2d4:	04b360b3 	mul	z19.s, z5.s, z19.s
  10f2d8:	04659673 	lsr	z19.s, z19.s, #27
  10f2dc:	046596d6 	lsr	z22.s, z22.s, #27
  10f2e0:	0e143e05 	mov	w5, v16.s[2]
  10f2e4:	05a03b50 	mov	z16.s, w26
  10f2e8:	04979096 	lslr	z22.s, p4/m, z22.s, z4.s
  10f2ec:	04979093 	lslr	z19.s, p4/m, z19.s, z4.s
  10f2f0:	04383273 	and	z19.d, z19.d, z24.d
  10f2f4:	043732d6 	and	z22.d, z22.d, z23.d
  10f2f8:	04b460d7 	mul	z23.s, z6.s, z20.s
  10f2fc:	04b460b4 	mul	z20.s, z5.s, z20.s
  10f300:	258092d6 	cmpne	p6.s, p4/z, z22.s, #0
  10f304:	25809277 	cmpne	p7.s, p4/z, z19.s, #0
  10f308:	a541ae73 	ld1w	{z19.s}, p3/z, [x19, #1, mul vl]
  10f30c:	a540aa76 	ld1w	{z22.s}, p2/z, [x19]
  10f310:	046596f7 	lsr	z23.s, z23.s, #27
  10f314:	04659694 	lsr	z20.s, z20.s, #27
  10f318:	056648e6 	uzp1	p6.h, p7.h, p6.h
  10f31c:	04979097 	lslr	z23.s, p4/m, z23.s, z4.s
  10f320:	04979094 	lslr	z20.s, p4/m, z20.s, z4.s
  10f324:	250654a6 	and	p6.b, p5/z, p5.b, p6.b
  10f328:	04373273 	and	z19.d, z19.d, z23.d
  10f32c:	250646b6 	mov	p6.b, p1/m, p5.b
  10f330:	254042c6 	nots	p6.b, p0/z, p6.b
  10f334:	1a9f17e7 	cset	w7, eq	// eq = none
  10f338:	25809276 	cmpne	p6.s, p4/z, z19.s, #0
  10f33c:	043432d3 	and	z19.d, z22.d, z20.d
  10f340:	04b560d6 	mul	z22.s, z6.s, z21.s
  10f344:	04b560b5 	mul	z21.s, z5.s, z21.s
  10f348:	a540aa94 	ld1w	{z20.s}, p2/z, [x20]
  10f34c:	25809277 	cmpne	p7.s, p4/z, z19.s, #0
  10f350:	a541ae93 	ld1w	{z19.s}, p3/z, [x20, #1, mul vl]
  10f354:	046596b5 	lsr	z21.s, z21.s, #27
  10f358:	046596d6 	lsr	z22.s, z22.s, #27
  10f35c:	056648e6 	uzp1	p6.h, p7.h, p6.h
  10f360:	04979096 	lslr	z22.s, p4/m, z22.s, z4.s
  10f364:	04979095 	lslr	z21.s, p4/m, z21.s, z4.s
  10f368:	250654a6 	and	p6.b, p5/z, p5.b, p6.b
  10f36c:	04353294 	and	z20.d, z20.d, z21.d
  10f370:	04363273 	and	z19.d, z19.d, z22.d
  10f374:	04b260d5 	mul	z21.s, z6.s, z18.s
  10f378:	04b260b2 	mul	z18.s, z5.s, z18.s
  10f37c:	250646b6 	mov	p6.b, p1/m, p5.b
  10f380:	04659652 	lsr	z18.s, z18.s, #27
  10f384:	254042c6 	nots	p6.b, p0/z, p6.b
  10f388:	1a9f17f3 	cset	w19, eq	// eq = none
  10f38c:	25809276 	cmpne	p6.s, p4/z, z19.s, #0
  10f390:	a541acd3 	ld1w	{z19.s}, p3/z, [x6, #1, mul vl]
  10f394:	25809297 	cmpne	p7.s, p4/z, z20.s, #0
  10f398:	a540a8d4 	ld1w	{z20.s}, p2/z, [x6]
  10f39c:	046596b5 	lsr	z21.s, z21.s, #27
  10f3a0:	04979095 	lslr	z21.s, p4/m, z21.s, z4.s
  10f3a4:	04979092 	lslr	z18.s, p4/m, z18.s, z4.s
  10f3a8:	056648e6 	uzp1	p6.h, p7.h, p6.h
  10f3ac:	250654a6 	and	p6.b, p5/z, p5.b, p6.b
  10f3b0:	04353273 	and	z19.d, z19.d, z21.d
  10f3b4:	04323292 	and	z18.d, z20.d, z18.d
  10f3b8:	04b160d4 	mul	z20.s, z6.s, z17.s
  10f3bc:	04b160b1 	mul	z17.s, z5.s, z17.s
  10f3c0:	250646b6 	mov	p6.b, p1/m, p5.b
  10f3c4:	254042c6 	nots	p6.b, p0/z, p6.b
  10f3c8:	1a9f17f4 	cset	w20, eq	// eq = none
  10f3cc:	25809276 	cmpne	p6.s, p4/z, z19.s, #0
  10f3d0:	25809257 	cmpne	p7.s, p4/z, z18.s, #0
  10f3d4:	a541ac92 	ld1w	{z18.s}, p3/z, [x4, #1, mul vl]
  10f3d8:	a540a893 	ld1w	{z19.s}, p2/z, [x4]
  10f3dc:	04659631 	lsr	z17.s, z17.s, #27
  10f3e0:	04659694 	lsr	z20.s, z20.s, #27
  10f3e4:	04979094 	lslr	z20.s, p4/m, z20.s, z4.s
  10f3e8:	04979091 	lslr	z17.s, p4/m, z17.s, z4.s
  10f3ec:	056648e6 	uzp1	p6.h, p7.h, p6.h
  10f3f0:	250654a6 	and	p6.b, p5/z, p5.b, p6.b
  10f3f4:	04313271 	and	z17.d, z19.d, z17.d
  10f3f8:	04343252 	and	z18.d, z18.d, z20.d
  10f3fc:	04b060d3 	mul	z19.s, z6.s, z16.s
  10f400:	04b060b0 	mul	z16.s, z5.s, z16.s
  10f404:	250646b6 	mov	p6.b, p1/m, p5.b
  10f408:	254042c6 	nots	p6.b, p0/z, p6.b
  10f40c:	1a9f17e6 	cset	w6, eq	// eq = none
  10f410:	25809256 	cmpne	p6.s, p4/z, z18.s, #0
  10f414:	25809237 	cmpne	p7.s, p4/z, z17.s, #0
  10f418:	a541ae11 	ld1w	{z17.s}, p3/z, [x16, #1, mul vl]
  10f41c:	a540aa12 	ld1w	{z18.s}, p2/z, [x16]
  10f420:	04659610 	lsr	z16.s, z16.s, #27
  10f424:	04659673 	lsr	z19.s, z19.s, #27
  10f428:	04979093 	lslr	z19.s, p4/m, z19.s, z4.s
  10f42c:	04979090 	lslr	z16.s, p4/m, z16.s, z4.s
  10f430:	056648e6 	uzp1	p6.h, p7.h, p6.h
  10f434:	250654a6 	and	p6.b, p5/z, p5.b, p6.b
  10f438:	04333231 	and	z17.d, z17.d, z19.d
  10f43c:	04303250 	and	z16.d, z18.d, z16.d
  10f440:	04a760d2 	mul	z18.s, z6.s, z7.s
  10f444:	04a760a7 	mul	z7.s, z5.s, z7.s
  10f448:	250646b6 	mov	p6.b, p1/m, p5.b
  10f44c:	046594e7 	lsr	z7.s, z7.s, #27
  10f450:	254042c6 	nots	p6.b, p0/z, p6.b
  10f454:	1a9f17e4 	cset	w4, eq	// eq = none
  10f458:	25809236 	cmpne	p6.s, p4/z, z17.s, #0
  10f45c:	a540aa51 	ld1w	{z17.s}, p2/z, [x18]
  10f460:	25809217 	cmpne	p7.s, p4/z, z16.s, #0
  10f464:	a541ae50 	ld1w	{z16.s}, p3/z, [x18, #1, mul vl]
  10f468:	04659652 	lsr	z18.s, z18.s, #27
  10f46c:	04979087 	lslr	z7.s, p4/m, z7.s, z4.s
  10f470:	04979092 	lslr	z18.s, p4/m, z18.s, z4.s
  10f474:	056648e6 	uzp1	p6.h, p7.h, p6.h
  10f478:	250654a6 	and	p6.b, p5/z, p5.b, p6.b
  10f47c:	04273227 	and	z7.d, z17.d, z7.d
  10f480:	04323210 	and	z16.d, z16.d, z18.d
  10f484:	a540aa31 	ld1w	{z17.s}, p2/z, [x17]
  10f488:	250646b6 	mov	p6.b, p1/m, p5.b
  10f48c:	254042c6 	nots	p6.b, p0/z, p6.b
  10f490:	1a9f17f0 	cset	w16, eq	// eq = none
  10f494:	258090f7 	cmpne	p7.s, p4/z, z7.s, #0
  10f498:	05a038a7 	mov	z7.s, w5
  10f49c:	25809216 	cmpne	p6.s, p4/z, z16.s, #0
  10f4a0:	a541ae30 	ld1w	{z16.s}, p3/z, [x17, #1, mul vl]
  10f4a4:	381fd1a7 	sturb	w7, [x13, #-3]
  10f4a8:	04a760c6 	mul	z6.s, z6.s, z7.s
  10f4ac:	04a760a5 	mul	z5.s, z5.s, z7.s
  10f4b0:	381fe1b3 	sturb	w19, [x13, #-2]
  10f4b4:	381ff1b4 	sturb	w20, [x13, #-1]
  10f4b8:	056648e6 	uzp1	p6.h, p7.h, p6.h
  10f4bc:	390001a6 	strb	w6, [x13]
  10f4c0:	390005a4 	strb	w4, [x13, #1]
  10f4c4:	390009b0 	strb	w16, [x13, #2]
  10f4c8:	250654a6 	and	p6.b, p5/z, p5.b, p6.b
  10f4cc:	046594a5 	lsr	z5.s, z5.s, #27
  10f4d0:	046594c6 	lsr	z6.s, z6.s, #27
  10f4d4:	250646b6 	mov	p6.b, p1/m, p5.b
  10f4d8:	254042c6 	nots	p6.b, p0/z, p6.b
  10f4dc:	04979086 	lslr	z6.s, p4/m, z6.s, z4.s
  10f4e0:	04979085 	lslr	z5.s, p4/m, z5.s, z4.s
  10f4e4:	1a9f17f2 	cset	w18, eq	// eq = none
  10f4e8:	39000db2 	strb	w18, [x13, #3]
  10f4ec:	04253225 	and	z5.d, z17.d, z5.d
  10f4f0:	04263206 	and	z6.d, z16.d, z6.d
  10f4f4:	258090d6 	cmpne	p6.s, p4/z, z6.s, #0
  10f4f8:	258090b7 	cmpne	p7.s, p4/z, z5.s, #0
  10f4fc:	056648e6 	uzp1	p6.h, p7.h, p6.h
  10f500:	250654a6 	and	p6.b, p5/z, p5.b, p6.b
  10f504:	250646b6 	mov	p6.b, p1/m, p5.b
  10f508:	254042c6 	nots	p6.b, p0/z, p6.b
  10f50c:	1a9f17f1 	cset	w17, eq	// eq = none
  10f510:	f1000529 	subs	x9, x9, #0x1
  10f514:	390011b1 	strb	w17, [x13, #4]
  10f518:	910021ad 	add	x13, x13, #0x8
  10f51c:	54ffe121 	b.ne	10f140 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0xc0>  // b.any
  10f520:	d37d084c 	ubfiz	x12, x2, #3, #3
  10f524:	b40024ec 	cbz	x12, 10f9c0 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x940>
  10f528:	927de049 	and	x9, x2, #0xffffffffffffff8
  10f52c:	f9400801 	ldr	x1, [x0, #16]
  10f530:	8b090d0d 	add	x13, x8, x9, lsl #3
  10f534:	f94001a8 	ldr	x8, [x13]
  10f538:	ca487908 	eor	x8, x8, x8, lsr #30
  10f53c:	9b0b7d08 	mul	x8, x8, x11
  10f540:	ca486d08 	eor	x8, x8, x8, lsr #27
  10f544:	9b0a7d08 	mul	x8, x8, x10
  10f548:	ca487d10 	eor	x16, x8, x8, lsr #31
  10f54c:	d360fe08 	lsr	x8, x16, #32
  10f550:	9b017d08 	mul	x8, x8, x1
  10f554:	d360fd08 	lsr	x8, x8, #32
  10f558:	eb01011f 	cmp	x8, x1
  10f55c:	54002742 	b.cs	10fa44 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9c4>  // b.hs, b.nlast
  10f560:	9240084f 	and	x15, x2, #0x7
  10f564:	b40027af 	cbz	x15, 10fa58 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9d8>
  10f568:	4e040e02 	dup	v2.4s, w16
  10f56c:	90000510 	adrp	x16, 1af000 <<clap_builder::builder::command::Command>::get_external_subcommand_value_parser::DEFAULT+0x30>
  10f570:	f940040e 	ldr	x14, [x0, #8]
  10f574:	4f000424 	movi	v4.4s, #0x1
  10f578:	3dc0e200 	ldr	q0, [x16, #896]
  10f57c:	90000510 	adrp	x16, 1af000 <<clap_builder::builder::command::Command>::get_external_subcommand_value_parser::DEFAULT+0x30>
  10f580:	3dc0e601 	ldr	q1, [x16, #912]
  10f584:	52800030 	mov	w16, #0x1                   	// #1
  10f588:	8b0815c8 	add	x8, x14, x8, lsl #5
  10f58c:	4ea09c43 	mul	v3.4s, v2.4s, v0.4s
  10f590:	4ea19c42 	mul	v2.4s, v2.4s, v1.4s
  10f594:	6f250463 	ushr	v3.4s, v3.4s, #27
  10f598:	6f250442 	ushr	v2.4s, v2.4s, #27
  10f59c:	6ea34483 	ushl	v3.4s, v4.4s, v3.4s
  10f5a0:	6ea24482 	ushl	v2.4s, v4.4s, v2.4s
  10f5a4:	ad401105 	ldp	q5, q4, [x8]
  10f5a8:	4e231c83 	and	v3.16b, v4.16b, v3.16b
  10f5ac:	4e221ca2 	and	v2.16b, v5.16b, v2.16b
  10f5b0:	4ea09863 	cmeq	v3.4s, v3.4s, #0
  10f5b4:	4ea09842 	cmeq	v2.4s, v2.4s, #0
  10f5b8:	4e431842 	uzp1	v2.8h, v2.8h, v3.8h
  10f5bc:	6e70a842 	umaxv	h2, v2.8h
  10f5c0:	1e260048 	fmov	w8, s2
  10f5c4:	0a280208 	bic	w8, w16, w8
  10f5c8:	38296868 	strb	w8, [x3, x9]
  10f5cc:	f100219f 	cmp	x12, #0x8
  10f5d0:	54001f80 	b.eq	10f9c0 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x940>  // b.none
  10f5d4:	f94005a8 	ldr	x8, [x13, #8]
  10f5d8:	ca487908 	eor	x8, x8, x8, lsr #30
  10f5dc:	9b0b7d08 	mul	x8, x8, x11
  10f5e0:	ca486d08 	eor	x8, x8, x8, lsr #27
  10f5e4:	9b0a7d08 	mul	x8, x8, x10
  10f5e8:	ca487d11 	eor	x17, x8, x8, lsr #31
  10f5ec:	d360fe28 	lsr	x8, x17, #32
  10f5f0:	9b017d08 	mul	x8, x8, x1
  10f5f4:	d360fd08 	lsr	x8, x8, #32
  10f5f8:	eb01011f 	cmp	x8, x1
  10f5fc:	54002242 	b.cs	10fa44 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9c4>  // b.hs, b.nlast
  10f600:	b2400130 	orr	x16, x9, #0x1
  10f604:	f10005ff 	cmp	x15, #0x1
  10f608:	54002260 	b.eq	10fa54 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9d4>  // b.none
  10f60c:	4e040e22 	dup	v2.4s, w17
  10f610:	8b0815c8 	add	x8, x14, x8, lsl #5
  10f614:	4f000424 	movi	v4.4s, #0x1
  10f618:	52800031 	mov	w17, #0x1                   	// #1
  10f61c:	4ea09c43 	mul	v3.4s, v2.4s, v0.4s
  10f620:	4ea19c42 	mul	v2.4s, v2.4s, v1.4s
  10f624:	6f250442 	ushr	v2.4s, v2.4s, #27
  10f628:	6f250463 	ushr	v3.4s, v3.4s, #27
  10f62c:	6ea34483 	ushl	v3.4s, v4.4s, v3.4s
  10f630:	6ea24482 	ushl	v2.4s, v4.4s, v2.4s
  10f634:	ad401105 	ldp	q5, q4, [x8]
  10f638:	4e231c83 	and	v3.16b, v4.16b, v3.16b
  10f63c:	4e221ca2 	and	v2.16b, v5.16b, v2.16b
  10f640:	4ea09863 	cmeq	v3.4s, v3.4s, #0
  10f644:	4ea09842 	cmeq	v2.4s, v2.4s, #0
  10f648:	4e431842 	uzp1	v2.8h, v2.8h, v3.8h
  10f64c:	6e70a842 	umaxv	h2, v2.8h
  10f650:	1e260048 	fmov	w8, s2
  10f654:	0a280228 	bic	w8, w17, w8
  10f658:	38306868 	strb	w8, [x3, x16]
  10f65c:	f100419f 	cmp	x12, #0x10
  10f660:	54001b00 	b.eq	10f9c0 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x940>  // b.none
  10f664:	f94009a8 	ldr	x8, [x13, #16]
  10f668:	ca487908 	eor	x8, x8, x8, lsr #30
  10f66c:	9b0b7d08 	mul	x8, x8, x11
  10f670:	ca486d08 	eor	x8, x8, x8, lsr #27
  10f674:	9b0a7d08 	mul	x8, x8, x10
  10f678:	ca487d11 	eor	x17, x8, x8, lsr #31
  10f67c:	d360fe28 	lsr	x8, x17, #32
  10f680:	9b017d08 	mul	x8, x8, x1
  10f684:	d360fd08 	lsr	x8, x8, #32
  10f688:	eb01011f 	cmp	x8, x1
  10f68c:	54001dc2 	b.cs	10fa44 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9c4>  // b.hs, b.nlast
  10f690:	b27f0130 	orr	x16, x9, #0x2
  10f694:	f10009ff 	cmp	x15, #0x2
  10f698:	54001de0 	b.eq	10fa54 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9d4>  // b.none
  10f69c:	4e040e22 	dup	v2.4s, w17
  10f6a0:	8b0815c8 	add	x8, x14, x8, lsl #5
  10f6a4:	4f000424 	movi	v4.4s, #0x1
  10f6a8:	52800031 	mov	w17, #0x1                   	// #1
  10f6ac:	4ea09c43 	mul	v3.4s, v2.4s, v0.4s
  10f6b0:	4ea19c42 	mul	v2.4s, v2.4s, v1.4s
  10f6b4:	6f250442 	ushr	v2.4s, v2.4s, #27
  10f6b8:	6f250463 	ushr	v3.4s, v3.4s, #27
  10f6bc:	6ea34483 	ushl	v3.4s, v4.4s, v3.4s
  10f6c0:	6ea24482 	ushl	v2.4s, v4.4s, v2.4s
  10f6c4:	ad401105 	ldp	q5, q4, [x8]
  10f6c8:	4e231c83 	and	v3.16b, v4.16b, v3.16b
  10f6cc:	4e221ca2 	and	v2.16b, v5.16b, v2.16b
  10f6d0:	4ea09863 	cmeq	v3.4s, v3.4s, #0
  10f6d4:	4ea09842 	cmeq	v2.4s, v2.4s, #0
  10f6d8:	4e431842 	uzp1	v2.8h, v2.8h, v3.8h
  10f6dc:	6e70a842 	umaxv	h2, v2.8h
  10f6e0:	1e260048 	fmov	w8, s2
  10f6e4:	0a280228 	bic	w8, w17, w8
  10f6e8:	38306868 	strb	w8, [x3, x16]
  10f6ec:	f100619f 	cmp	x12, #0x18
  10f6f0:	54001680 	b.eq	10f9c0 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x940>  // b.none
  10f6f4:	f9400da8 	ldr	x8, [x13, #24]
  10f6f8:	ca487908 	eor	x8, x8, x8, lsr #30
  10f6fc:	9b0b7d08 	mul	x8, x8, x11
  10f700:	ca486d08 	eor	x8, x8, x8, lsr #27
  10f704:	9b0a7d08 	mul	x8, x8, x10
  10f708:	ca487d11 	eor	x17, x8, x8, lsr #31
  10f70c:	d360fe28 	lsr	x8, x17, #32
  10f710:	9b017d08 	mul	x8, x8, x1
  10f714:	d360fd08 	lsr	x8, x8, #32
  10f718:	eb01011f 	cmp	x8, x1
  10f71c:	54001942 	b.cs	10fa44 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9c4>  // b.hs, b.nlast
  10f720:	b2400530 	orr	x16, x9, #0x3
  10f724:	f1000dff 	cmp	x15, #0x3
  10f728:	54001960 	b.eq	10fa54 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9d4>  // b.none
  10f72c:	4e040e22 	dup	v2.4s, w17
  10f730:	8b0815c8 	add	x8, x14, x8, lsl #5
  10f734:	4f000424 	movi	v4.4s, #0x1
  10f738:	52800031 	mov	w17, #0x1                   	// #1
  10f73c:	4ea09c43 	mul	v3.4s, v2.4s, v0.4s
  10f740:	4ea19c42 	mul	v2.4s, v2.4s, v1.4s
  10f744:	6f250442 	ushr	v2.4s, v2.4s, #27
  10f748:	6f250463 	ushr	v3.4s, v3.4s, #27
  10f74c:	6ea34483 	ushl	v3.4s, v4.4s, v3.4s
  10f750:	6ea24482 	ushl	v2.4s, v4.4s, v2.4s
  10f754:	ad401105 	ldp	q5, q4, [x8]
  10f758:	4e231c83 	and	v3.16b, v4.16b, v3.16b
  10f75c:	4e221ca2 	and	v2.16b, v5.16b, v2.16b
  10f760:	4ea09863 	cmeq	v3.4s, v3.4s, #0
  10f764:	4ea09842 	cmeq	v2.4s, v2.4s, #0
  10f768:	4e431842 	uzp1	v2.8h, v2.8h, v3.8h
  10f76c:	6e70a842 	umaxv	h2, v2.8h
  10f770:	1e260048 	fmov	w8, s2
  10f774:	0a280228 	bic	w8, w17, w8
  10f778:	38306868 	strb	w8, [x3, x16]
  10f77c:	f100819f 	cmp	x12, #0x20
  10f780:	54001200 	b.eq	10f9c0 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x940>  // b.none
  10f784:	f94011a8 	ldr	x8, [x13, #32]
  10f788:	ca487908 	eor	x8, x8, x8, lsr #30
  10f78c:	9b0b7d08 	mul	x8, x8, x11
  10f790:	ca486d08 	eor	x8, x8, x8, lsr #27
  10f794:	9b0a7d08 	mul	x8, x8, x10
  10f798:	ca487d11 	eor	x17, x8, x8, lsr #31
  10f79c:	d360fe28 	lsr	x8, x17, #32
  10f7a0:	9b017d08 	mul	x8, x8, x1
  10f7a4:	d360fd08 	lsr	x8, x8, #32
  10f7a8:	eb01011f 	cmp	x8, x1
  10f7ac:	540014c2 	b.cs	10fa44 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9c4>  // b.hs, b.nlast
  10f7b0:	b27e0130 	orr	x16, x9, #0x4
  10f7b4:	f10011ff 	cmp	x15, #0x4
  10f7b8:	540014e0 	b.eq	10fa54 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9d4>  // b.none
  10f7bc:	4e040e22 	dup	v2.4s, w17
  10f7c0:	8b0815c8 	add	x8, x14, x8, lsl #5
  10f7c4:	4f000424 	movi	v4.4s, #0x1
  10f7c8:	52800031 	mov	w17, #0x1                   	// #1
  10f7cc:	4ea09c43 	mul	v3.4s, v2.4s, v0.4s
  10f7d0:	4ea19c42 	mul	v2.4s, v2.4s, v1.4s
  10f7d4:	6f250442 	ushr	v2.4s, v2.4s, #27
  10f7d8:	6f250463 	ushr	v3.4s, v3.4s, #27
  10f7dc:	6ea34483 	ushl	v3.4s, v4.4s, v3.4s
  10f7e0:	6ea24482 	ushl	v2.4s, v4.4s, v2.4s
  10f7e4:	ad401105 	ldp	q5, q4, [x8]
  10f7e8:	4e231c83 	and	v3.16b, v4.16b, v3.16b
  10f7ec:	4e221ca2 	and	v2.16b, v5.16b, v2.16b
  10f7f0:	4ea09863 	cmeq	v3.4s, v3.4s, #0
  10f7f4:	4ea09842 	cmeq	v2.4s, v2.4s, #0
  10f7f8:	4e431842 	uzp1	v2.8h, v2.8h, v3.8h
  10f7fc:	6e70a842 	umaxv	h2, v2.8h
  10f800:	1e260048 	fmov	w8, s2
  10f804:	0a280228 	bic	w8, w17, w8
  10f808:	38306868 	strb	w8, [x3, x16]
  10f80c:	f100a19f 	cmp	x12, #0x28
  10f810:	54000d80 	b.eq	10f9c0 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x940>  // b.none
  10f814:	f94015a8 	ldr	x8, [x13, #40]
  10f818:	ca487908 	eor	x8, x8, x8, lsr #30
  10f81c:	9b0b7d08 	mul	x8, x8, x11
  10f820:	ca486d08 	eor	x8, x8, x8, lsr #27
  10f824:	9b0a7d08 	mul	x8, x8, x10
  10f828:	ca487d11 	eor	x17, x8, x8, lsr #31
  10f82c:	d360fe28 	lsr	x8, x17, #32
  10f830:	9b017d08 	mul	x8, x8, x1
  10f834:	d360fd08 	lsr	x8, x8, #32
  10f838:	eb01011f 	cmp	x8, x1
  10f83c:	54001042 	b.cs	10fa44 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9c4>  // b.hs, b.nlast
  10f840:	528000b0 	mov	w16, #0x5                   	// #5
  10f844:	aa100130 	orr	x16, x9, x16
  10f848:	f10015ff 	cmp	x15, #0x5
  10f84c:	54001040 	b.eq	10fa54 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9d4>  // b.none
  10f850:	4e040e22 	dup	v2.4s, w17
  10f854:	8b0815c8 	add	x8, x14, x8, lsl #5
  10f858:	4f000424 	movi	v4.4s, #0x1
  10f85c:	52800031 	mov	w17, #0x1                   	// #1
  10f860:	4ea09c43 	mul	v3.4s, v2.4s, v0.4s
  10f864:	4ea19c42 	mul	v2.4s, v2.4s, v1.4s
  10f868:	6f250442 	ushr	v2.4s, v2.4s, #27
  10f86c:	6f250463 	ushr	v3.4s, v3.4s, #27
  10f870:	6ea34483 	ushl	v3.4s, v4.4s, v3.4s
  10f874:	6ea24482 	ushl	v2.4s, v4.4s, v2.4s
  10f878:	ad401105 	ldp	q5, q4, [x8]
  10f87c:	4e231c83 	and	v3.16b, v4.16b, v3.16b
  10f880:	4e221ca2 	and	v2.16b, v5.16b, v2.16b
  10f884:	4ea09863 	cmeq	v3.4s, v3.4s, #0
  10f888:	4ea09842 	cmeq	v2.4s, v2.4s, #0
  10f88c:	4e431842 	uzp1	v2.8h, v2.8h, v3.8h
  10f890:	6e70a842 	umaxv	h2, v2.8h
  10f894:	1e260048 	fmov	w8, s2
  10f898:	0a280228 	bic	w8, w17, w8
  10f89c:	38306868 	strb	w8, [x3, x16]
  10f8a0:	f100c19f 	cmp	x12, #0x30
  10f8a4:	540008e0 	b.eq	10f9c0 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x940>  // b.none
  10f8a8:	f94019a8 	ldr	x8, [x13, #48]
  10f8ac:	ca487908 	eor	x8, x8, x8, lsr #30
  10f8b0:	9b0b7d08 	mul	x8, x8, x11
  10f8b4:	ca486d08 	eor	x8, x8, x8, lsr #27
  10f8b8:	9b0a7d08 	mul	x8, x8, x10
  10f8bc:	ca487d10 	eor	x16, x8, x8, lsr #31
  10f8c0:	d360fe08 	lsr	x8, x16, #32
  10f8c4:	9b017d08 	mul	x8, x8, x1
  10f8c8:	d360fd08 	lsr	x8, x8, #32
  10f8cc:	eb01011f 	cmp	x8, x1
  10f8d0:	54000ba2 	b.cs	10fa44 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9c4>  // b.hs, b.nlast
  10f8d4:	b27f0529 	orr	x9, x9, #0x6
  10f8d8:	f10019ff 	cmp	x15, #0x6
  10f8dc:	54000be0 	b.eq	10fa58 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9d8>  // b.none
  10f8e0:	4e040e02 	dup	v2.4s, w16
  10f8e4:	8b0815c8 	add	x8, x14, x8, lsl #5
  10f8e8:	4f000424 	movi	v4.4s, #0x1
  10f8ec:	52800030 	mov	w16, #0x1                   	// #1
  10f8f0:	4ea09c43 	mul	v3.4s, v2.4s, v0.4s
  10f8f4:	4ea19c42 	mul	v2.4s, v2.4s, v1.4s
  10f8f8:	6f250442 	ushr	v2.4s, v2.4s, #27
  10f8fc:	6f250463 	ushr	v3.4s, v3.4s, #27
  10f900:	6ea34483 	ushl	v3.4s, v4.4s, v3.4s
  10f904:	6ea24482 	ushl	v2.4s, v4.4s, v2.4s
  10f908:	ad401105 	ldp	q5, q4, [x8]
  10f90c:	4e231c83 	and	v3.16b, v4.16b, v3.16b
  10f910:	4e221ca2 	and	v2.16b, v5.16b, v2.16b
  10f914:	4ea09863 	cmeq	v3.4s, v3.4s, #0
  10f918:	4ea09842 	cmeq	v2.4s, v2.4s, #0
  10f91c:	4e431842 	uzp1	v2.8h, v2.8h, v3.8h
  10f920:	6e70a842 	umaxv	h2, v2.8h
  10f924:	1e260048 	fmov	w8, s2
  10f928:	0a280208 	bic	w8, w16, w8
  10f92c:	38296868 	strb	w8, [x3, x9]
  10f930:	f100e19f 	cmp	x12, #0x38
  10f934:	54000460 	b.eq	10f9c0 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x940>  // b.none
  10f938:	f9401da8 	ldr	x8, [x13, #56]
  10f93c:	ca487908 	eor	x8, x8, x8, lsr #30
  10f940:	9b0b7d08 	mul	x8, x8, x11
  10f944:	ca486d08 	eor	x8, x8, x8, lsr #27
  10f948:	9b0a7d08 	mul	x8, x8, x10
  10f94c:	ca487d0a 	eor	x10, x8, x8, lsr #31
  10f950:	d360fd48 	lsr	x8, x10, #32
  10f954:	9b017d08 	mul	x8, x8, x1
  10f958:	d360fd08 	lsr	x8, x8, #32
  10f95c:	eb01011f 	cmp	x8, x1
  10f960:	54000722 	b.cs	10fa44 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9c4>  // b.hs, b.nlast
  10f964:	b2400849 	orr	x9, x2, #0x7
  10f968:	f1001dff 	cmp	x15, #0x7
  10f96c:	54000760 	b.eq	10fa58 <<lanefilter::BlockedFilter>::check_batch_lanes_masked+0x9d8>  // b.none
  10f970:	4e040d42 	dup	v2.4s, w10
  10f974:	8b0815c8 	add	x8, x14, x8, lsl #5
  10f978:	5280002a 	mov	w10, #0x1                   	// #1
  10f97c:	4ea09c40 	mul	v0.4s, v2.4s, v0.4s
  10f980:	4ea19c41 	mul	v1.4s, v2.4s, v1.4s
  10f984:	4f000422 	movi	v2.4s, #0x1
  10f988:	6f250421 	ushr	v1.4s, v1.4s, #27
  10f98c:	6f250400 	ushr	v0.4s, v0.4s, #27
  10f990:	6ea04440 	ushl	v0.4s, v2.4s, v0.4s
  10f994:	6ea14441 	ushl	v1.4s, v2.4s, v1.4s
  10f998:	ad400903 	ldp	q3, q2, [x8]
  10f99c:	4e201c40 	and	v0.16b, v2.16b, v0.16b
  10f9a0:	4e211c61 	and	v1.16b, v3.16b, v1.16b
  10f9a4:	4ea09800 	cmeq	v0.4s, v0.4s, #0
  10f9a8:	4ea09821 	cmeq	v1.4s, v1.4s, #0
  10f9ac:	4e401820 	uzp1	v0.8h, v1.8h, v0.8h
  10f9b0:	6e70a800 	umaxv	h0, v0.8h
  10f9b4:	1e260008 	fmov	w8, s0
  10f9b8:	0a280148 	bic	w8, w10, w8
  10f9bc:	38296868 	strb	w8, [x3, x9]
  10f9c0:	a9464ff4 	ldp	x20, x19, [sp, #96]
  10f9c4:	a94557f6 	ldp	x22, x21, [sp, #80]
  10f9c8:	a9445ff8 	ldp	x24, x23, [sp, #64]
  10f9cc:	a94367fa 	ldp	x26, x25, [sp, #48]
  10f9d0:	f94013fb 	ldr	x27, [sp, #32]
  10f9d4:	a9417bfd 	ldp	x29, x30, [sp, #16]
  10f9d8:	9101c3ff 	add	sp, sp, #0x70
  10f9dc:	d65f03c0 	ret
  10f9e0:	d0000845 	adrp	x5, 219000 <anon.afad092435d08350a526eed223d9f0ee.15.llvm.6830234897814459200+0x130>
  10f9e4:	913a20a5 	add	x5, x5, #0xe88
  10f9e8:	910023e1 	add	x1, sp, #0x8
  10f9ec:	910063a2 	add	x2, x29, #0x18
  10f9f0:	2a1f03e0 	mov	w0, wzr
  10f9f4:	aa1f03e3 	mov	x3, xzr
  10f9f8:	97fc050a 	bl	10e20 <core::panicking::assert_failed::<usize, usize>>
  10f9fc:	eb01027f 	cmp	x19, x1
  10fa00:	9a942268 	csel	x8, x19, x20, cs	// cs = hs, nlast
  10fa04:	eb0100ff 	cmp	x7, x1
  10fa08:	9a8820e8 	csel	x8, x7, x8, cs	// cs = hs, nlast
  10fa0c:	eb0100df 	cmp	x6, x1
  10fa10:	9a8420c9 	csel	x9, x6, x4, cs	// cs = hs, nlast
  10fa14:	7100023f 	cmp	w17, #0x0
  10fa18:	9a891112 	csel	x18, x8, x9, ne	// ne = any
  10fa1c:	710000bf 	cmp	w5, #0x0
  10fa20:	d0000842 	adrp	x2, 219000 <anon.afad092435d08350a526eed223d9f0ee.15.llvm.6830234897814459200+0x130>
  10fa24:	913ae042 	add	x2, x2, #0xeb8
  10fa28:	9a901240 	csel	x0, x18, x16, ne	// ne = any
  10fa2c:	97fc055a 	bl	10f94 <core::panicking::panic_bounds_check>
  10fa30:	710000bf 	cmp	w5, #0x0
  10fa34:	d0000842 	adrp	x2, 219000 <anon.afad092435d08350a526eed223d9f0ee.15.llvm.6830234897814459200+0x130>
  10fa38:	913ae042 	add	x2, x2, #0xeb8
  10fa3c:	9a911240 	csel	x0, x18, x17, ne	// ne = any
  10fa40:	97fc0555 	bl	10f94 <core::panicking::panic_bounds_check>
  10fa44:	d0000842 	adrp	x2, 219000 <anon.afad092435d08350a526eed223d9f0ee.15.llvm.6830234897814459200+0x130>
  10fa48:	913b4042 	add	x2, x2, #0xed0
  10fa4c:	aa0803e0 	mov	x0, x8
  10fa50:	97fc0551 	bl	10f94 <core::panicking::panic_bounds_check>
  10fa54:	aa1003e9 	mov	x9, x16
  10fa58:	d0000848 	adrp	x8, 219000 <anon.afad092435d08350a526eed223d9f0ee.15.llvm.6830234897814459200+0x130>
  10fa5c:	913a8108 	add	x8, x8, #0xea0
  10fa60:	aa0903e0 	mov	x0, x9
  10fa64:	aa0203e1 	mov	x1, x2
  10fa68:	aa0803e2 	mov	x2, x8
  10fa6c:	97fc054a 	bl	10f94 <core::panicking::panic_bounds_check>

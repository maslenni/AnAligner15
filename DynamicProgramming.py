def GetAlignmentBySimilarityMatrix(similarityMatrix):
	dpTableRows = len(similarityMatrix) + 1
	dpTableCols = len(similarityMatrix[0]) + 1
	dpTable = [[0 for x in range(dpTableCols)] for x in range(dpTableRows)]
	gapPenalty = 0

	for i in range(1, dpTableCols):
		dpTable[0][i] = i * gapPenalty
	for i in range(1, dpTableRows):
		dpTable[i][0] = i * gapPenalty

	for i in range(1, dpTableRows):
		for j in range(1, dpTableCols):
			score = similarityMatrix[i - 1][j - 1]
			scoreDiag = dpTable[i -1][j -1] + score
			scoreUp = dpTable[i - 1][j] + gapPenalty
			scoreLeft = dpTable[i][j - 1] + gapPenalty
			scoreMax = max(scoreDiag, scoreUp, scoreLeft)
			dpTable[i][j] = scoreMax

	alignment = []
	i = dpTableRows - 1
	j = dpTableCols - 1
	while i > 0 and j > 0:
		print(i, j)
		similarity = similarityMatrix[i - 1][j - 1]
		score = dpTable[i][j]
		scoreDiag = dpTable[i -1][j -1] + similarity
		scoreUp = dpTable[i - 1][j] + gapPenalty
		scoreLeft = dpTable[i][j - 1] + gapPenalty
		if score == scoreDiag:
			alignment.insert(0, [i, j])
			i -= 1
			j -= 1
		elif score == scoreLeft:
			#alignment.insert(0, [i, None])
			j -= 1 
		elif score == scoreUp:
			#alignment.insert(0, [None, j])
			i -= 1
			
	return alignment
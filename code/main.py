import glob
import os
import sys
import csv
import json
import time

import numpy as np
import scipy as sp
import scipy.signal

import matplotlib
import matplotlib.pyplot as plt

import datetime
from cycler import cycler

import sklearn.manifold

import otu
    
    
def ubiomeAnalysis():
    #---------------------------------------------------------------------------
    # Directory of where your json files are
    baseDir = r'..\sample_data'
    #baseDir = r'C:\Users\Isaac\Desktop\New folder (2)'
    #---------------------------------------------------------------------------
    
    # Get all applicable files
    fn = glob.glob(os.path.join(baseDir,'*.json'))
    
    # Sort files by time
    samplingTime = []
    phyla = []
    for f in fn:
        r = open(f).read()
        o = json.loads(r)
        samplingTime.append(o['sampling_time'])   
        
    # Convert samplingTime to datetime object
    rr = []
    for k in samplingTime:
        tmp = datetime.datetime(int(k[0:4]), int(k[5:7]), int(k[8:10]))
        rr.append(tmp)        
        
    # Sort files by sampling time
    order = np.argsort(np.array(rr))
    fn = [fn[i] for i in order]
    samplingTime = [samplingTime[i] for i in order]
    rr = [rr[i] for i in order]
    
    phyla = []
    for f in fn:
        r = open(f).read()
        o = json.loads(r)        
        lst = o['ubiome_bacteriacounts']
        for k in lst:
            if k['tax_rank'] == 'phylum':
                phyla.append(k['tax_name'])

    phyla = set(phyla)  
    
    # Get counts for each phyla from each dataset
    N = len(fn)
    p = {}
    for k in phyla:
        p[k] = np.zeros(N)
        c = 0
        for f in fn:
            r = open(f).read()
            lst = json.loads(r)['ubiome_bacteriacounts'] 
            for kk in lst:
                if kk['tax_rank'] == 'phylum' and kk['tax_name'] == k:
                    p[kk['tax_name']][c] =  kk['count_norm']/10000
            c += 1

    otuList = []
    for k in fn:
        myOtu = otu.OTU(k)
        otuList.append(myOtu)
    
    # Get phyla distribution
    phylum = []
    for k in otuList:
        phylum += k.getTaxonomy('phylum')[0]
    phylum = list(set(phylum))

    numPhylum = len(phylum)    
    numFiles = len(fn)
    r = np.zeros((numPhylum, numFiles))
    for k, fileIdx in zip(otuList, range(numFiles)):
        ph = k.getTaxonomy('phylum')
        idx = None
        for ppp, d in zip(ph[0], ph[1]):
            for pp,i in zip(phylum, range(numPhylum)):
                if ppp == pp:
                    r[i, fileIdx] = d
                    break
    
    

    r = []
    phyla = sorted(list(phyla))
    for k in range(N):
        for kk in phyla:
            r.append(p[kk][k])
    r = np.reshape(r, (len(phyla), N), order='F')

    

    plt.rc('axes', prop_cycle=(cycler('color', ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00' , '#cab2d6', '#6a3d9a' , '#ffff99', '#b15928'])))
    plt.rc('lines', **{'marker':'o'})

    order = np.argsort(np.sum(r, axis=1))[::-1]
    r = r[order.astype('int'),:]
    
    phyla = [ phyla[i] for i in order]

    # ----------------------------------
    # Phyla-level plots
    # ----------------------------------
    # Stack plot
    plt.stackplot(rr, r)    
    #plt.legend(phyla)
    plt.legend(phyla, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.ylim([0,100])
    plt.title('Phyla Percent of Sample, Stacked')
    plt.ylabel('Percent of Sample')
    plt.xlabel('Date')
    plt.savefig(os.path.join(baseDir, 'phyla percent of sample - stacked.png'))

    # F/B ratio
    fIdx = phyla.index('Firmicutes')
    bIdx = phyla.index('Bacteroidetes')
    plt.clf()
    plt.title('Firmicutes to Bacteroidetes Ratio')
    plt.xlabel('Sample Date')
    plt.plot(rr, r[fIdx,:] / r[bIdx,:]);
    plt.savefig(os.path.join(baseDir, 'Firmicutes to Bacteroidetes Ratio.png'))
    
    # Phyla percent
    plt.clf()
    plt.plot(rr, r.T);
    plt.title('Phyla Percent of Sample')
    plt.ylabel('Percent of Sample')
    plt.xlabel('Date')
    plt.ylim([0,100])
    plt.legend(phyla, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.savefig(os.path.join(baseDir, 'phyla percent of sample.png'))    
    # ----------------------------------

    
    allData = {}
    for f in fn:
        r = open(f).read()
        o = json.loads(r)
        lst = o['ubiome_bacteriacounts']
        for k in lst:
            allData[k['taxon']] = {'parent' : k['parent'], 'tax_name':k['tax_name'], 'tax_rank':k['tax_rank']}    
    
    # Pull all genii
    genii = []
    geniiFullName = []
    for f in fn:
        r = open(f).read()
        o = json.loads(r)
        lst = o['ubiome_bacteriacounts']
        for k in lst:
            if k['tax_rank'] == 'genus':
                # Phylum, family, genus
                if k['tax_name'] == 'Actinomyces':
                    print('here')
                phylum = ''
                family = ''
                tmp = k['parent']
                while True:
                    if allData[tmp]['tax_rank'] != 'phylum':
                        tmp = allData[tmp]['parent']
                    else:
                        phylum = allData[tmp]['tax_name']
                        break
                tmp = k['parent']
                while True:
                    if tmp == 0:
                        family = 'None'
                        break
                    if allData[tmp]['tax_rank'] != 'family':
                        tmp = allData[tmp]['parent']
                    else:
                        family = allData[tmp]['tax_name']
                        break    
                genii.append(phylum +'-'+ family + '-'+ k['tax_name'])

    genii = sorted(list(set(genii)))    
    
    # Get counts for each species from each dataset
    N = len(fn)
    p = {}
    for k in genii:
        p[k] = np.zeros(N)
        c = 0
        for f in fn:
            r = open(f).read()
            lst = json.loads(r)['ubiome_bacteriacounts'] 
            for kk in lst:
                name = k[k.rfind('-')+1:]
                if kk['tax_rank'] == 'genus' and kk['tax_name'] == name:
                    p[k][c] =  kk['count_norm']/10000
            c += 1    

    plt.clf()
    plt.title('Percentage of Probiotic Strains')
    c = []
    
    if 'Actinobacteria-Bifidobacteriaceae-Bifidobacterium' not in p.keys():
        p['Actinobacteria-Bifidobacteriaceae-Bifidobacterium'] = np.zeros(N)
    c.append(p['Actinobacteria-Bifidobacteriaceae-Bifidobacterium'])
        
    if 'Firmicutes-Lactobacillaceae-Lactobacillus' not in p.keys():
        p['Firmicutes-Lactobacillaceae-Lactobacillus'] = np.zeros(N)
    c.append(p['Firmicutes-Lactobacillaceae-Lactobacillus'])
                        
    if 'Firmicutes-Leuconostocaceae-Leuconostoc' not in p.keys():
        p['Firmicutes-Leuconostocaceae-Leuconostoc'] = np.zeros(N)
    c.append(p['Firmicutes-Leuconostocaceae-Leuconostoc'])
                            
    if 'Firmicutes-Streptococcaceae-Lactococcus' not in p.keys():
        p['Firmicutes-Streptococcaceae-Lactococcus'] = np.zeros(N)
    c.append(p['Firmicutes-Streptococcaceae-Lactococcus'])
                            

    plt.stackplot(rr, c)
    plt.legend(['Actinobacteria-Bifidobacteriaceae-Bifidobacterium', 'Firmicutes-Lactobacillaceae-Lactobacillus', 'Firmicutes-Leuconostocaceae-Leuconostoc', 'Firmicutes-Streptococcaceae-Lactococcus'], \
               bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.xlabel('Sample Date')
    plt.savefig(os.path.join(baseDir, 'Percentage of Probiotic Strains.png'))
    
    plt.clf()
    if 'Euryarchaeota-Methanobacteriaceae-Methanosphaera' not in p.keys():
        p['Euryarchaeota-Methanobacteriaceae-Methanosphaera'] = np.zeros(N)
    plt.title('Percentage of Methane Producing Strains Connected to SIBO')    
    plt.plot(rr, p['Euryarchaeota-Methanobacteriaceae-Methanosphaera'])  #p['Euryarchaeota-Methanobacteriaceae-Methanobrevibacter']);
    plt.xlabel('Sample Date')
    plt.savefig(os.path.join(baseDir, 'Percentage of Methane Producing Strains.png'))
    
    r = []
    for k in range(N):
        for kk in genii:
            r.append(p[kk][k])
    r = np.reshape(r, (len(genii), N), order='F')   
    
    plt.clf()
    plt.matshow(r, aspect='auto', cmap=matplotlib.cm.get_cmap('Blues', 9), norm=matplotlib.colors.LogNorm(vmin=0.1, vmax=100)); plt.colorbar()
    plt.yticks(np.arange(r.shape[0]), genii, size='xx-small')
    plt.xlabel('Sample Number'); plt.grid(False)
    plt.title('Genus Heatmap [Percent]')
    plt.savefig(os.path.join(baseDir, 'genus heatmap.png'))
    plt.close()
    
    plt.clf() 
    plt.matshow(r, aspect='auto', cmap=matplotlib.cm.get_cmap('cubehelix_r', 9), norm=matplotlib.colors.LogNorm(vmin=0.1, vmax=100)); plt.colorbar()
    plt.yticks(np.arange(r.shape[0]), genii, size='xx-small')
    plt.xlabel('Sample Number'); plt.grid(False)
    plt.title('Genus Heatmap [Percent]')
    plt.savefig(os.path.join(baseDir, 'genus heatmap - alt colormap.png'))
    plt.close()
    
    plt.clf()
    almPlot = r - np.median(r, axis=1).reshape(r.shape[0],1)
    mx = np.max(np.abs([almPlot.max(), almPlot.min()]))
    plt.matshow(almPlot, aspect='auto', cmap=matplotlib.cm.get_cmap('bwr_r', 21), vmin=-mx, vmax=mx); 
    plt.yticks(np.arange(r.shape[0]), genii, size='xx-small')
    plt.xlabel('Sample Number'); plt.grid(False)
    plt.title('Genus Almplot\nGain = Blue, Loss = Red')
    plt.savefig(os.path.join(baseDir, 'genus almplot.png'))
    plt.close()  
    
    # number of genii counts
    plt.clf()
    plt.plot(rr, np.sum(r,axis=0))
    plt.title('Percent of Genii Identified in Sample')
    plt.xlabel('Sample Date')
    plt.ylim([0, 100])
    plt.savefig(os.path.join(baseDir, 'percent of genii identified.png'))      
                

    # fetch list from URL
    #Download list from wikipedia
    urlPos = r'https://en.wikipedia.org/wiki/Category:Gram-positive_bacteria'
    urlNeg = r'https://en.wikipedia.org/wiki/Category:Gram-negative_bacteria'

    import urllib.request
    response = urllib.request.urlopen(urlPos)
    data = response.read()      # a `bytes` object
    textPos = data.decode('utf-8') 
    textPos = textPos[textPos.find('Pages in category "Gram-positive bacteria"'):]
    response = urllib.request.urlopen(urlNeg)
    data = response.read()      # a `bytes` object
    textNeg = data.decode('utf-8')   
    textNeg = textNeg[textNeg.find('Pages in category "Gram-negative bacteria"'):]
    gp = np.zeros(N)
    gn = np.zeros(N)
    gu = np.zeros(N)# unknown
    for k in range(N):
        for kk in genii:
            genus = kk[kk.rfind('-')+1:]
            phylum = kk[:kk.find('-')]
            if textPos.find(genus) > -1 or textPos.find(phylum) > -1:
                gp[k] += p[kk][k]
            elif textNeg.find(genus) > -1 or textNeg.find(phylum) > -1:
                gn[k] += p[kk][k] 
            else:
                gu[k] += p[kk][k] 
                print(kk)
            if (textPos.find(genus) > -1 or textPos.find(phylum) > -1) and (textNeg.find(genus) > -1 or textNeg.find(phylum) > -1):
                print('both')
            
            #r.append(p[kk][k])
    #r = np.reshape(r, (len(genii), N), order='F')    
    
    plt.clf()
    plt.title('Gram +/-')
    plt.stackplot(rr, np.row_stack((gp,gn,gu)));
    plt.xlabel('Sample Date')
    plt.legend(['Gram+', 'Gram-', 'Gram Unknown'], bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.savefig(os.path.join(baseDir, 'gram pos neg - stacked.png'))
    
    r = []
    for k in range(N):
        for kk in genii:
            r.append(p[kk][k])
    r = np.reshape(r, (len(genii), N), order='F')      
    
    # Pull all family
    family = []
    for f in fn:
        r = open(f).read()
        o = json.loads(r)
        lst = o['ubiome_bacteriacounts']
        for k in lst:
            if k['tax_rank'] == 'family':
                family.append(k['tax_name'])

    family = sorted(list(set(family)))        
    
    # Get counts for each family from each dataset
    N = len(fn)
    p = {}
    for k in family:
        p[k] = np.zeros(N)
        c = 0
        for f in fn:
            r = open(f).read()
            lst = json.loads(r)['ubiome_bacteriacounts'] 
            for kk in lst:
                name = k[k.rfind('-')+1:]
                if kk['tax_rank'] == 'family' and kk['tax_name'] == name:
                    p[k][c] =  kk['count_norm']/10000
            c += 1      
    
    r = []
    for k in range(N):
        for kk in family:
            r.append(p[kk][k])
    r = np.reshape(r, (len(family), N), order='F')         
    
    plt.clf()
    r_int = np.round(r*10000)
    #N = np.sum(r_int, axis=0)
    D = np.sum(r_int*(r_int-1), axis=0) /  (np.sum(r_int, axis=0)*(np.sum(r_int, axis=0)-1))
    #D = np.sum((r/100)**2,axis=0) # old way
    #p = (r/np.sum(r, axis=0))
    #D = 1/np.sum(p**2, axis=0)          
    plt.plot(rr, 10*(1-D))
    plt.title('Simpsons Diversity Index - (from Family)')
    plt.xlabel('Sample Date')
    plt.ylim([0,10])
    plt.savefig(os.path.join(baseDir, 'simpsons diversity index.png'))     
    
    plt.clf()
    plt.stackplot(rr, r)
    plt.legend(family, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.ylim([0,100])
    plt.title('Family Percent of Sample, Stacked')
    plt.ylabel('Percent of Sample')
    plt.xlabel('Date')
    plt.savefig(os.path.join(baseDir, 'family percent of sample - stacked.png'))        
            
    # Similarity among all samples
    numSamples = len(rr)
    ref = np.median(r, axis=1)
    mat = np.zeros((numSamples, ))
    for k in range(numSamples):
        mat[k] = np.corrcoef(ref, r[:,k])[1,0]
    plt.clf()
    plt.plot(rr, mat)
    #plt.legend(family, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.ylim([0,1])
    plt.title('Family Similarity Compared to Median')
    plt.ylabel('Similarity [0,1]')
    plt.xlabel('Date')
    plt.savefig(os.path.join(baseDir, 'family similarity to median.png'))    
    
    plt.clf()
    f = sklearn.manifold.MDS()
    f.fit(r.T)
    v = f.fit_transform(r.T)
    labels = ['{0}'.format(time.strftime('%b %d %Y', rr[i].timetuple())) for i in range(numSamples)]
    plt.scatter(v[:,0], v[:,1])
    plt.title('Cluster Analysis')
    for label, x, y in zip(labels, v[:,0], v[:,1]):
        plt.annotate(label, xy=(x,y), xytext=(-10, -10), textcoords = 'offset points', size = 7, ha = 'right', va = 'bottom',
        bbox = dict(boxstyle = 'round,pad=0.5', fc = 'blue', alpha = 0.5),
        arrowprops = dict(arrowstyle = 'wedge', connectionstyle = 'arc3,rad=-0.3'))
    plt.savefig(os.path.join(baseDir, 'cluster analysis.png')) 
            
    # Pull all species
    species = []
    for f in fn:
        r = open(f).read()
        o = json.loads(r)
        lst = o['ubiome_bacteriacounts']
        for k in lst:
            if k['tax_rank'] == 'species':
                species.append(k['tax_name'])

    species = sorted(list(set(species)))    
    
    # Pull all species
    species = []
    for f in fn:
        r = open(f).read()
        o = json.loads(r)
        lst = o['ubiome_bacteriacounts']
        for k in lst:
            if k['tax_rank'] == 'species':
                species.append(k['tax_name'])

    species = sorted(list(set(species)))

    # Get counts for each species from each dataset
    N = len(fn)
    p = {}
    for k in species:
        p[k] = np.zeros(N)
        c = 0
        for f in fn:
            r = open(f).read()
            lst = json.loads(r)['ubiome_bacteriacounts'] 
            for kk in lst:
                if kk['tax_rank'] == 'species' and kk['tax_name'] == k:
                    p[kk['tax_name']][c] =  kk['count_norm']/10000
            c += 1

    r = []
    for k in range(N):
        for kk in species:
            r.append(p[kk][k])
    r = np.reshape(r, (len(species), N), order='F')   
    

    # Show pathogens
    #Download list from wikipedia
    url = r'https://en.wikipedia.org/wiki/Pathogenic_bacteria#List_of_genera_of_pathogenic_bacteria_and_microscopy_features'
    
    import urllib.request
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8')    

    pathogenicStrains = []
    for strain in p.keys():
        # If 2 words, take second word
        strainFull = strain
        if strain.find(' ') >= 0:
            strain = strain[strain.find(' ')+1:]
        if strain == 'sp.': 
            continue
        if text.find(' ' + strain) >= 0:
            pathogenicStrains.append(strainFull)

    plt.clf()
    plt.title('Percentage Pathogenic Strains')
    c = []
    for k in pathogenicStrains:
        c.append(p[k])
    plt.stackplot(rr, c)
    plt.xlabel('Sample Date')
    plt.legend(pathogenicStrains, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.savefig(os.path.join(baseDir, 'pathogenic strains - stacked.png'))
    

    # SHow the dominant 10 species
    s = np.sum(r, axis=1)
    idx = np.argsort(s)[-10:]
    rsub = r[idx, :]
    leg = [species[idx[k]] for k in range(10)]
    plt.clf()
    plt.stackplot(rr, np.flipud(rsub));
    plt.title('Top 10 Species Percent of Sample')
    plt.ylabel('Percent of Sample')
    plt.xlabel('Date')
    plt.ylim([0,np.sum(rsub,axis=0).max()]); #plt.yscale('log')
    plt.legend(leg[::-1], bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.savefig(os.path.join(baseDir, 'top 10 species percent of sample - stacked.png'))
    
    # SHow the least dominate 10 species
    s = np.sum(r, axis=1)
    idx = np.argsort(s)[0:10]
    rsub = r[idx, :]
    leg = [species[idx[k]] for k in range(10)]
    plt.clf()
    plt.stackplot(rr, np.flipud(rsub));
    plt.title('Bottom 10 Species Percent of Sample')
    plt.ylabel('Percent of Sample')
    plt.xlabel('Date')
    plt.ylim([0,np.sum(rsub,axis=0).max()]); #plt.yscale('log')
    plt.legend(leg[::-1], bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.savefig(os.path.join(baseDir, 'bottom 10 species percent of sample - stacked.png'))
    
    # number of species counts
    plt.clf()
    plt.plot(rr, np.sum(r,axis=0))
    plt.title('Percent of Species Identified in Sample')
    plt.xlabel('Sample Date')
    plt.ylim([0, 100])
    plt.savefig(os.path.join(baseDir, 'percent of species identified.png'))
    
    return

def parseOtu():
    fn = r'..\cfs_data\otu_table_mc2_w_tax_even32233.txt'
    fid = open(fn)
    line = fid.readline()
    subjects = (fid.readline()).split('\t')
    subjects = subjects[1:-1]
    numSubjects = len(subjects)
    mat = []
    otus = []
    while True:
        line = (fid.readline()).split('\t')
        otus.append(line[-1])        
        if line[0] is '':
            break
        mat.append(np.array([float(i) for i in line[1:-1]]))
    mat = np.array(mat)
    
    # Compare at the family level
    # Gather all families
    families = []
    for k in range(len(otus)):
        tmp = otus[k].split(';')
        if len(tmp) >= 5:
            if len(tmp[4])>4:
                family = str.strip(tmp[4][4:])
                family = family.replace('[','')
                family = family.replace(']','')
                families.append(family)
    
    families = set(families)
    numFamilies = len(families)
    rr = np.zeros((numFamilies, numSubjects))
    # Gather up rows for a specific family
    idx = 0
    for k in otus:
        famId = 0
        for family in families:
            if k.find(family)>-1:
                rr[famId, :] += mat[idx,:]
                break
            famId += 1
        idx += 1
    
    # Normalize
    rr = rr / np.sum(rr, axis=0)[np.newaxis]
    
    # read in control vs patients
    fid = open(r'..\cfs_data\mapping_metadata_CFS.txt')
    reader = csv.DictReader(fid, delimiter='\t')
    controls = []
    patients = []
    idx = 0
    for row in reader:
        if row['Subject'] == 'Control':  
            controls.append(row['#SampleID'])
        if row['Subject'] == 'Patient':  
            patients.append(row['#SampleID'])    
            
    controlsIdx = []
    patientsIdx = []
    for k in range(len(subjects)):
        for kk in controls:
            if subjects[k] == kk:
                controlsIdx.append(k)
        for kk in patients:
            if subjects[k] == kk:
                patientsIdx.append(k)                

    patientsIdx = np.array(patientsIdx)
    controlsIdx = np.array(controlsIdx)
    controlMat = rr[:,controlsIdx]
    patientMat = rr[:,patientsIdx]
    inputMat = np.hstack((patientMat, controlMat))
    outputVec = np.hstack((np.ones(patientMat.shape[1]), -np.ones(controlMat.shape[1])))

    # Affinity Matrix
    numSubjects = inputMat.shape[1]
    aff_mat = np.zeros((numSubjects, numSubjects))
    for k in range(numSubjects):
        for kk in range(numSubjects):
            aff_mat[k,kk] = 1/np.sqrt(np.sum((inputMat[:,k] - inputMat[:,kk])**2))
    plt.figure()
    plt.imshow(aff_mat)
    plt.show()
    
    from sklearn.lda import LDA
    clf = LDA()
    clf.fit(inputMat[:,1:80].T, outputVec[1:80])    
    fit = clf.predict(inputMat.T)
    err = np.sum(np.abs(fit - outputVec)>0)
    print(err)
    
    # SVM
    clf = sklearn.svm.SVC(kernel='linear', C=1e-1)
    n_samples = inputMat.shape[1]
    cv = sklearn.cross_validation.KFold(n_samples,n_folds=8,shuffle=True)
    scores = sklearn.cross_validation.cross_val_score(clf, inputMat.T, outputVec, cv=cv)
    
    # Predict my data
    # Read in my data file
    myOtu = otu.OTU(r'..\sample_data\01112016.json')
    
    # Get family distribution
    gen = myOtu.getTaxonomy('genus')    
    
    myOtu.mergeTaxonomy('family', families)
    myOtu.getDistribution('family')
    
    # Do LDA fit
    # run predictor

    return

if __name__ == "__main__":
    # https://raw.githubusercontent.com/CamDavidsonPilon/Probabilistic-Programming-and-Bayesian-Methods-for-Hackers/master/styles/matplotlibrc
    #matplotlib.style.use('https://raw.githubusercontent.com/CamDavidsonPilon/Probabilistic-Programming-and-Bayesian-Methods-for-Hackers/master/styles/matplotlibrc')
    matplotlib.style.use('https://raw.githubusercontent.com/isaacgerg/matplotlibrc/master/matplotlibrc.txt')
    
    ubiomeAnalysis()
    
    parseOtu()
   
    print('Done.')
    

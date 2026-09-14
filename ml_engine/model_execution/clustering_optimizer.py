from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score



class ClusteringOptimizer:


    def find_best_k(self,X,min_k=2,max_k=10):
        best_k = None
        best_score = -1


        for k in range(min_k,max_k + 1):

            model = KMeans(n_clusters=k,random_state=42)
            labels = model.fit_predict(X)
            score = silhouette_score(X,labels)

            if score > best_score:

                best_score = score

                best_k = k



        return {

            "n_clusters": best_k,

            "silhouette_score": best_score

        }
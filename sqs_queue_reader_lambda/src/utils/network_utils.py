import networkx as nx
from itertools import combinations


def old_fn_create_complete_network(network_data):
    print("Graph Algorithm Calculation -  Building Graph")
    G = nx.Graph()
    # Creating Node
    for ind_node, wt_list in network_data['nodes'].items():
        G.add_node(ind_node, weight=sum(wt_list), size=sum(wt_list))
    # Adding Edges
    for (node1, node2), wt_list in network_data['edges'].items():
        G.add_edge(node1, node2, weight=min(wt_list))
    graph_results = {}
    # Closeness Centrality Calculation
    print("Graph Algorithm Calculation -  Centrality Score")
    centrality_score = nx.closeness_centrality(G, distance='weight')
    graph_results['closeness_centrality'] = {k: v for k, v in sorted(centrality_score.items(),
                                                                     key=lambda item: item[1], reverse=True)}
    # Page Rank Calculation
    #print("Graph Algorithm Calculation -  Pagerank Score")
    #pagerank_score = nx.pagerank(G, weight='weight')
    #graph_results['pagerank'] = {k: v for k, v in sorted(pagerank_score.items(), key=lambda item: item[1], reverse=True)}
    return graph_results


def fn_create_overall_indedges(word_counter, network_data, network_type='Concepts'):
    # Create Nodes
    for word, count in word_counter.items():
        network_data[network_type]['nodes'].setdefault(word, []).append(count)
    # Create Edges
    for ind_comb in combinations(sorted(list(word_counter.keys())), 2):
        total_occurance = sum([word_counter[ind_comb[0]] + word_counter[ind_comb[1]]])
        network_data[network_type]['edges'].setdefault(ind_comb, []).append(total_occurance)
    return network_data


def fn_create_pplconcept_indedges(word_counter, network_data, assignee, network_type='PeopleConcepts'):
    # Create Nodes
    node_name = "People|{}".format(assignee)
    network_data[network_type]['nodes'].setdefault(node_name, []).append(1)

    # Create Edges
    for word, count in word_counter.items():
        network_data[network_type]['nodes'].setdefault(word, []).append(count)
        people_name = "People|{}".format(assignee)
        network_data[network_type]['edges'].setdefault((people_name, word), []).append(count)

    return network_data


def fn_create_complete_network(network_data):
    #print("Graph Algorithm Calculation -  Building Graph")
    G = {}
    for ind_graphtype, network_scores in network_data.items():
        G[ind_graphtype] = nx.Graph()
        # Creating Node
        for ind_node, wt_list in network_scores['nodes'].items():
            G[ind_graphtype].add_node(ind_node, weight=sum(wt_list), size=sum(wt_list))
        # Adding Edges
        for (node1, node2), wt_list in network_scores['edges'].items():
            G[ind_graphtype].add_edge(node1, node2, weight=max(wt_list))

    #print("Total No of Concept Nodes {}".format(len(list(G['Concepts'].nodes()))))
    #print("Total No of People Concept Nodes {}".format(len(list(G['PeopleConcepts'].nodes()))))
    return G


def fn_additional_concepts(G, reqd_keywords):
    all_keywords = []
    for keyword_source_counter in range(0, len(reqd_keywords)):
        source_keyword = reqd_keywords[keyword_source_counter]
        for keyword_target_counter in range(keyword_source_counter + 1, len(reqd_keywords)):
            target_keyword = reqd_keywords[keyword_target_counter]
            #print("Source {} Target: {}".format(source_keyword, target_keyword))
            try:
                length, reqd_keywordpaths = nx.bidirectional_dijkstra(G['Concepts'], source=source_keyword,
                                                                      target=target_keyword, weight='weight')
                #print("Path Found")
            except:
                print("Unable to Find Path - Skipped", source_keyword, '->', target_keyword)
                continue
            #print("Source: ", source_keyword, '->', "Target: ", target_keyword, "Length: ", length, "All Keywords: ",
            #      reqd_keywordpaths)
            all_keywords.extend(reqd_keywordpaths)
    # ppl_concept_keywords = []
    all_keywords = list(set(all_keywords))
    return all_keywords


def fn_conceptppl_subgraph(G, keywords):
    ppl_concept_subgraph = nx.subgraph(G['PeopleConcepts'], keywords).copy()
    isolates = list(nx.isolates(ppl_concept_subgraph))
    #print('->', len(list(isolates)), list(isolates))
    ppl_concept_subgraph.remove_nodes_from(list(isolates))
    return ppl_concept_subgraph


def fn_calc_pagerank(G, graph_weight='weight'):
    pagerank_score = nx.pagerank(G, weight=graph_weight)
    pagerank_score = {k: v for k, v in sorted(pagerank_score.items(), key=lambda item: item[1], reverse=True)}
    return pagerank_score


def fn_analyze_issuedesc(G, reqd_keywords):
    #print(id, len(reqd_keywords), reqd_keywords)
    ppl_keywords = fn_additional_concepts(G, reqd_keywords)
    #print("Total no of Additional Keywords {}".format(len(ppl_keywords)))
    ppl_concept_keywords = list(ppl_keywords)
    ppl_concept_keywords.extend([i for i in list(G['PeopleConcepts'].nodes()) if 'People' in i])
    #print("Total no of Additional Keywords and People {}".format(len(ppl_concept_keywords)))

    ppl_concept_subgraph = fn_conceptppl_subgraph(G, ppl_concept_keywords)
    #print("People Concept", len(list(G['PeopleConcepts'].nodes())), "PeopleKeywords", len(ppl_concept_keywords),
    #      "SubGraph Concepts", len(list(ppl_concept_subgraph.nodes())))
    subgraph_pagerank_dict = fn_calc_pagerank(ppl_concept_subgraph, graph_weight='weight')
    reqd_ppl = [key.split('|')[-1] for key, val in subgraph_pagerank_dict.items() if "People|" in key]
    return ppl_keywords, reqd_ppl


from wordcloud import WordCloud
import matplotlib.pyplot as plt


def fn_plot_wordcloud(wrd_freq, file_path):
    wordcloud = WordCloud()
    wordcloud.generate_from_frequencies(frequencies=wrd_freq)
    plt.figure()
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    print("Saving wordcloud to {}".format(file_path))
    plt.savefig(file_path)
